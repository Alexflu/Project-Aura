#include "AuraRigActor.h"
#include "AuraBehaviorComponent.h"
#include "AuraPaths.h"
#include "Components/PoseableMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"

AAuraRigActor::AAuraRigActor()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("StageRoot"));
    Body = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("RiggedBody"));
    Body->SetupAttachment(RootComponent);
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetRelativeRotation(FRotator(0, -90, 0));
    Behavior = CreateDefaultSubobject<UAuraBehaviorComponent>(TEXT("Behavior"));
}

void AAuraRigActor::BeginPlay()
{
    Super::BeginPlay();
    StageOrigin = GetActorLocation();
    AddTickPrerequisiteComponent(Behavior);
    Body->AddTickPrerequisiteActor(this);
    StartedAt = FPlatformTime::Seconds();
    bTelemetry = FParse::Param(FCommandLine::Get(), TEXT("AuraTelemetry"));
    if (bTelemetry)
    {
        TelemetryPath = FPaths::Combine(AuraDataDirectory(), TEXT("runtime.jsonl"));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(TelemetryPath), true);
        FFileHelper::SaveStringToFile(TEXT(""), *TelemetryPath);
    }
    USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, *SkeletalMeshPath);
    if (!Mesh)
    {
        RigError = FString::Printf(TEXT("Missing skeletal mesh: %s. Run tools/unreal_body.py prepare."), *SkeletalMeshPath);
        UE_LOG(LogTemp, Error, TEXT("Aura: %s"), *RigError);
        return;
    }
    Body->SetSkinnedAssetAndUpdate(Mesh);
    const FReferenceSkeleton& Skeleton = Mesh->GetRefSkeleton();
    ReferenceLocal = Skeleton.GetRefBonePose();
    BoneCount = ReferenceLocal.Num();
    Pose.SetNum(BoneCount);
    for (int32 Index = 0; Index < BoneCount; ++Index)
    {
        BoneNames.Add(Skeleton.GetBoneName(Index));
        Parents.Add(Skeleton.GetParentIndex(Index));
    }
    for (const FName Required : {FName("pelvis"), FName("head"), FName("upperarm_r"), FName("thigh_l"), FName("thigh_r")})
    {
        if (Skeleton.FindBoneIndex(Required) == INDEX_NONE)
        {
            RigError = FString::Printf(TEXT("Mannequin harness requires bone %s"), *Required.ToString());
            UE_LOG(LogTemp, Error, TEXT("Aura: %s"), *RigError);
            return;
        }
    }
    bRigReady = true;
    UE_LOG(LogTemp, Display, TEXT("Aura: rig ready, %d bones, %s"), BoneCount, *Mesh->GetName());
    UpdatePose(0);
}

void AAuraRigActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    RecordSample(DeltaSeconds);
    if (!bRigReady) return;
    // A disconnected or paused producer holds the complete pose and position.
    if (!Behavior->bConnected || Behavior->bPaused) return;
    const FVector Target = StageOrigin + Behavior->PositionCm;
    const FVector Step = Target - GetActorLocation();
    SetActorLocation(FMath::VInterpTo(GetActorLocation(), Target, DeltaSeconds, 12));
    if (Behavior->bMoving && Step.SizeSquared2D() > 1)
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), Step.Rotation(), DeltaSeconds, 5));
    else if (!Behavior->bMoving)
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), FRotator::ZeroRotator, DeltaSeconds, 3));
    MotionTime += FMath::Min(DeltaSeconds, .1f);
    UpdatePose(DeltaSeconds);
}

void AAuraRigActor::UpdatePose(float DeltaSeconds)
{
    WalkWeight = FMath::FInterpTo(WalkWeight, Behavior->bMoving ? 1.f : 0.f, DeltaSeconds, 7);
    WaveWeight = FMath::FInterpTo(WaveWeight, Behavior->Gesture == TEXT("wave") ? 1.f : 0.f, DeltaSeconds, 7);
    const FVector Look = GetActorTransform().InverseTransformPosition(StageOrigin + Behavior->GazeTargetCm) - FVector(0, 0, 160);
    GazeYaw = FMath::FInterpTo(GazeYaw, FMath::Clamp(static_cast<float>(FMath::RadiansToDegrees(FMath::Atan2(Look.Y, Look.X))), -55.f, 55.f), DeltaSeconds, 4);
    GazePitch = FMath::FInterpTo(GazePitch, FMath::Clamp(static_cast<float>(FMath::RadiansToDegrees(FMath::Atan2(Look.Z, Look.Size2D()))), -20.f, 25.f), DeltaSeconds, 4);
    const float Stride = FMath::Sin(MotionTime * 6) * WalkWeight;
    const float Breath = FMath::Sin(MotionTime * 1.8f);
    const bool Attentive = Behavior->Posture == TEXT("attentive") || Behavior->Mode == TEXT("listening");
    for (int32 Index = 0; Index < BoneCount; ++Index)
    {
        const FName Name = BoneNames[Index];
        FTransform Local = ReferenceLocal[Index];
        if (Name == TEXT("pelvis"))
            Local.AddToTranslation(FVector(0, 0, .5f * Breath + 1.2f * FMath::Abs(Stride)));
        Pose[Index] = Parents[Index] == INDEX_NONE ? Local : Local * Pose[Parents[Index]];
        FQuat Offset = FQuat::Identity;
        auto Rotate = [&Offset](FVector Axis, float Degrees)
        { Offset = FQuat(Axis, FMath::DegreesToRadians(Degrees)) * Offset; };
        // Mannequin mesh faces +Y before its -90-degree component rotation.
        if (Name == TEXT("spine_01")) Rotate(FVector::XAxisVector, (Attentive ? 4.f : 0.f) + Breath * .7f);
        if (Name == TEXT("head"))
        {
            Rotate(FVector::ZAxisVector, GazeYaw);
            Rotate(FVector::XAxisVector, GazePitch + (Behavior->Gesture == TEXT("nod") ? FMath::Sin(MotionTime * 8) * 10 : 0));
        }
        if (Name == TEXT("thigh_l")) Rotate(FVector::XAxisVector, Stride * 22);
        if (Name == TEXT("thigh_r")) Rotate(FVector::XAxisVector, -Stride * 22);
        if (Name == TEXT("calf_l")) Rotate(FVector::XAxisVector, -FMath::Max(0.f, Stride) * 28);
        if (Name == TEXT("calf_r")) Rotate(FVector::XAxisVector, -FMath::Max(0.f, -Stride) * 28);
        if (Name == TEXT("upperarm_l"))
        {
            Rotate(FVector::YAxisVector, 35);
            Rotate(FVector::XAxisVector, -Stride * 12);
        }
        if (Name == TEXT("upperarm_r"))
        {
            Rotate(FVector::YAxisVector, -35 + 110 * WaveWeight);
            Rotate(FVector::XAxisVector, Stride * 12 * (1 - WaveWeight));
        }
        if (Name == TEXT("lowerarm_r")) Rotate(FVector::YAxisVector, 35 * WaveWeight);
        if (Name == TEXT("hand_r")) Rotate(FVector::YAxisVector, FMath::Sin(MotionTime * 10) * 18 * WaveWeight);
        Pose[Index].SetRotation((Offset * Pose[Index].GetRotation()).GetNormalized());
        // Write all local transforms together. Per-bone component-space setters
        // would use the previous frame's parent transforms while posing children.
        Body->BoneSpaceTransforms[Index] = Parents[Index] == INDEX_NONE ? Pose[Index]
            : Pose[Index].GetRelativeTransform(Pose[Parents[Index]]);
    }
    Body->MarkRefreshTransformDirty();
}

void AAuraRigActor::RecordSample(float DeltaSeconds)
{
    const double Now = FPlatformTime::Seconds();
    // Explicit development diagnostics, bounded to two minutes at 10 Hz.
    if (!bTelemetry || Now - StartedAt > 120 || Now - LastSample < .1) return;
    LastSample = Now;
    TSharedRef<FJsonObject> Data = MakeShared<FJsonObject>();
    Data->SetNumberField(TEXT("elapsed_s"), Now - StartedAt);
    Data->SetNumberField(TEXT("frame_ms"), DeltaSeconds * 1000);
    Data->SetBoolField(TEXT("rig_ready"), bRigReady);
    Data->SetNumberField(TEXT("bones"), BoneCount);
    Data->SetBoolField(TEXT("connected"), Behavior->bConnected);
    Data->SetBoolField(TEXT("paused"), Behavior->bPaused);
    Data->SetStringField(TEXT("mode"), Behavior->Mode);
    Data->SetStringField(TEXT("gesture"), Behavior->Gesture);
    Data->SetStringField(TEXT("error"), Behavior->LastError);
    Data->SetNumberField(TEXT("mouth"), Behavior->MouthOpen);
    Data->SetNumberField(TEXT("x"), GetActorLocation().X);
    Data->SetNumberField(TEXT("y"), GetActorLocation().Y);
    Data->SetNumberField(TEXT("head_yaw"), GazeYaw);
    Data->SetNumberField(TEXT("wave_weight"), WaveWeight);
    Data->SetNumberField(TEXT("walk_weight"), WalkWeight);
    if (bRigReady)
    {
        Data->SetNumberField(TEXT("right_hand_z"), Body->GetBoneLocationByName(TEXT("hand_r"), EBoneSpaces::WorldSpace).Z);
        Data->SetNumberField(TEXT("left_foot_z"), Body->GetBoneLocationByName(TEXT("foot_l"), EBoneSpaces::WorldSpace).Z);
        Data->SetNumberField(TEXT("pelvis_z"), Body->GetBoneLocationByName(TEXT("pelvis"), EBoneSpaces::WorldSpace).Z);
    }
    FString Line;
    TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
        TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Line);
    FJsonSerializer::Serialize(Data, Writer);
    FFileHelper::SaveStringToFile(Line + TEXT("\n"), *TelemetryPath,
        FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append);
}
