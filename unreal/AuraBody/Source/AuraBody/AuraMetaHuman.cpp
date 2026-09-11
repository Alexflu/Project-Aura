#include "AuraMetaHuman.h"
#include "AuraBehaviorComponent.h"
#include "AuraRigActor.h"
#include "AuraPaths.h"
#include "Animation/AnimInstanceProxy.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

namespace
{
class FAuraMetaHumanProxy : public FAnimInstanceProxy
{
public:
    FAuraMetaHumanProxy(UAnimInstance* Instance) : FAnimInstanceProxy(Instance) {}
    TArray<FTransform> LocalPose;
    float Jaw = 0;
    float Smile = 0;
    bool bFace = false;

    virtual void PreUpdate(UAnimInstance* Instance, float DeltaSeconds) override
    {
        FAnimInstanceProxy::PreUpdate(Instance, DeltaSeconds);
        const UAuraMetaHumanAnim* Anim = CastChecked<UAuraMetaHumanAnim>(Instance);
        bFace = Anim->bFace;
        const auto* State = Anim->Behavior.Get();
        const bool Active = State && State->bConnected && !State->bPaused;
        Jaw = Active ? State->MouthOpen : 0;
        Smile = Active && State->Expression == TEXT("happy") ? State->ExpressionIntensity : 0;
        const USkeletalMesh* TargetMesh = GetSkelMeshComponent()->GetSkeletalMeshAsset();
        const USkinnedMeshComponent* Source = Anim->PoseSource;
        const USkeletalMesh* SourceMesh = Source ? Cast<USkeletalMesh>(Source->GetSkinnedAsset()) : nullptr;
        if (!TargetMesh || !SourceMesh) { LocalPose.Reset(); return; }
        const FReferenceSkeleton& TargetRef = TargetMesh->GetRefSkeleton();
        const FReferenceSkeleton& SourceRef = SourceMesh->GetRefSkeleton();
        const TArray<FTransform>& SourcePose = Source->GetComponentSpaceTransforms();
        TArray<FTransform> SourceReference = SourceRef.GetRefBonePose();
        for (int32 I = 0; I < SourceReference.Num(); ++I)
        {
            const int32 Parent = SourceRef.GetParentIndex(I);
            if (Parent != INDEX_NONE) SourceReference[I] *= SourceReference[Parent];
        }
        LocalPose = TargetRef.GetRefBonePose();
        TArray<FTransform> TargetReference = LocalPose;
        TArray<FTransform> ComponentPose;
        ComponentPose.SetNum(LocalPose.Num());
        for (int32 I = 0; I < LocalPose.Num(); ++I)
        {
            const int32 Parent = TargetRef.GetParentIndex(I);
            if (Parent != INDEX_NONE) TargetReference[I] *= TargetReference[Parent];
            ComponentPose[I] = Parent == INDEX_NONE ? LocalPose[I] : LocalPose[I] * ComponentPose[Parent];
            const FName Name = TargetRef.GetBoneName(I);
            const int32 SourceIndex = SourceRef.FindBoneIndex(Name);
            if (SourcePose.IsValidIndex(SourceIndex) && SourceReference.IsValidIndex(SourceIndex))
            {
                // Retarget rotation deltas, preserving this character's proportions.
                const FQuat Delta = SourcePose[SourceIndex].GetRotation() * SourceReference[SourceIndex].GetRotation().Inverse();
                ComponentPose[I].SetRotation((Delta * TargetReference[I].GetRotation()).GetNormalized());
                if (Name == TEXT("pelvis"))
                    ComponentPose[I].AddToTranslation(SourcePose[SourceIndex].GetTranslation() - SourceReference[SourceIndex].GetTranslation());
            }
            LocalPose[I] = Parent == INDEX_NONE ? ComponentPose[I] : ComponentPose[I].GetRelativeTransform(ComponentPose[Parent]);
        }
    }

    virtual bool Evaluate(FPoseContext& Output) override
    {
        Output.ResetToRefPose();
        const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
        for (const FCompactPoseBoneIndex Index : Output.Pose.ForEachBoneIndex())
        {
            const int32 MeshIndex = Bones.MakeMeshPoseIndex(Index).GetInt();
            if (LocalPose.IsValidIndex(MeshIndex)) Output.Pose[Index] = LocalPose[MeshIndex];
        }
        if (bFace)
        {
            // MetaHuman's existing post-process RigLogic consumes these GUI curves.
            Output.Curve.Set(TEXT("CTRL_expressions_jawOpen"), Jaw);
            Output.Curve.Set(TEXT("CTRL_expressions_mouthCornerPullL"), Smile);
            Output.Curve.Set(TEXT("CTRL_expressions_mouthCornerPullR"), Smile);
        }
        return true;
    }
};
}

FAnimInstanceProxy* UAuraMetaHumanAnim::CreateAnimInstanceProxy() { return new FAuraMetaHumanProxy(this); }
void UAuraMetaHumanAnim::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) { delete Proxy; }

UAuraMetaHuman::UAuraMetaHuman()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UAuraMetaHuman::BeginPlay()
{
    Super::BeginPlay();
    AAuraRigActor* Driver = Cast<AAuraRigActor>(GetOwner());
    if (!Driver || !Driver->bRigReady) return;
    UClass* Class = LoadClass<AActor>(nullptr, TEXT("/Game/MetaHumans/AuraPrototype_Ada/BP_AuraPrototype_Ada.BP_AuraPrototype_Ada_C"));
    if (!Class) { UE_LOG(LogTemp, Error, TEXT("Aura MetaHuman: assemble and audit the local prototype first")); return; }
    Character = GetWorld()->SpawnActor<AActor>(Class, Driver->GetActorTransform());
    if (!Character) return;
    Character->AttachToActor(Driver, FAttachmentTransformRules::KeepWorldTransform);
    // The assembled MetaHuman faces +Y; stage actors face +X.
    Character->SetActorRelativeRotation(FRotator(0, -90, 0));
    TArray<USkeletalMeshComponent*> Meshes;
    Character->GetComponents(Meshes);
    for (USkeletalMeshComponent* Mesh : Meshes)
    {
        if (Mesh->GetFName() == TEXT("Body")) Body = Mesh;
        if (Mesh->GetFName() == TEXT("Face")) Face = Mesh;
    }
    if (!Body || !Face || Body->GetNumBones() < 20 || Face->GetBoneIndex(TEXT("FACIAL_C_Jaw")) == INDEX_NONE)
    {
        UE_LOG(LogTemp, Error, TEXT("Aura MetaHuman: required body/face skeleton missing"));
        Character->Destroy();
        return;
    }
    Driver->Body->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    for (USkeletalMeshComponent* Mesh : {Body.Get(), Face.Get()})
    {
        Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
        Mesh->bEnableUpdateRateOptimizations = false;
        Mesh->SetAnimInstanceClass(UAuraMetaHumanAnim::StaticClass());
        UAuraMetaHumanAnim* Anim = CastChecked<UAuraMetaHumanAnim>(Mesh->GetAnimInstance());
        Anim->PoseSource = Mesh == Body ? static_cast<USkinnedMeshComponent*>(Driver->Body.Get()) : Body.Get();
        Anim->Behavior = Driver->Behavior;
        Anim->bFace = Mesh == Face;
        Mesh->AddTickPrerequisiteComponent(Anim->PoseSource);
    }
    Driver->Body->SetVisibility(false, false);
    AddTickPrerequisiteComponent(Face);
    bReady = true;
    StartedAt = FPlatformTime::Seconds();
    if (FParse::Param(FCommandLine::Get(), TEXT("AuraTelemetry")))
    {
        TelemetryPath = FPaths::Combine(AuraDataDirectory(), TEXT("metahuman-runtime.jsonl"));
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(TelemetryPath), true);
        FFileHelper::SaveStringToFile(TEXT(""), *TelemetryPath);
    }
    UE_LOG(LogTemp, Display, TEXT("Aura MetaHuman: live adapter ready (%d body / %d face bones)"), Body->GetNumBones(), Face->GetNumBones());
}

void UAuraMetaHuman::TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(Dt, TickType, TickFunction);
    const double Now = FPlatformTime::Seconds();
    if (!bReady || TelemetryPath.IsEmpty() || Now - StartedAt > 120 || Now - LastSample < .1) return;
    LastSample = Now;
    auto Driver = CastChecked<AAuraRigActor>(GetOwner());
    TSharedRef<FJsonObject> Data = MakeShared<FJsonObject>();
    Data->SetNumberField(TEXT("elapsed_s"), Now - StartedAt);
    Data->SetBoolField(TEXT("connected"), Driver->Behavior->bConnected);
    Data->SetBoolField(TEXT("paused"), Driver->Behavior->bPaused);
    Data->SetNumberField(TEXT("mouth"), Driver->Behavior->MouthOpen);
    Data->SetNumberField(TEXT("jaw_curve"), Face->GetAnimInstance()->GetCurveValue(TEXT("CTRL_expressions_jawOpen")));
    Data->SetNumberField(TEXT("jaw_z"), Face->GetBoneLocation(TEXT("FACIAL_C_Jaw"), EBoneSpaces::ComponentSpace).Z);
    Data->SetNumberField(TEXT("jaw_angle"), Face->GetSocketTransform(TEXT("FACIAL_C_Jaw"), RTS_ParentBoneSpace).Rotator().Pitch);
    const FQuat JawRotation = Face->GetSocketTransform(TEXT("FACIAL_C_Jaw"), RTS_ParentBoneSpace).GetRotation();
    Data->SetNumberField(TEXT("jaw_rotation_degrees"), FMath::RadiansToDegrees(JawRotation.AngularDistance(FQuat::Identity)));
    Data->SetNumberField(TEXT("wrist_z"), Body->GetBoneLocation(TEXT("hand_r"), EBoneSpaces::ComponentSpace).Z);
    Data->SetNumberField(TEXT("x"), Character->GetActorLocation().X);
    FString Line;
    auto Writer = TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Line);
    FJsonSerializer::Serialize(Data, Writer);
    FFileHelper::SaveStringToFile(Line + TEXT("\n"), *TelemetryPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM,
        &IFileManager::Get(), FILEWRITE_Append);
}
