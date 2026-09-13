#include "AuraWardrobe.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Actor.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

bool IsAuraGarmentCompatible(const FReferenceSkeleton& Body, const FReferenceSkeleton& Garment, FString& Reason)
{
    Reason.Reset();
    if (Garment.GetNum() == 0) { Reason = TEXT("empty skeleton"); return false; }
    for (int32 I = 0; I < Garment.GetNum(); ++I)
    {
        const FName Name = Garment.GetBoneName(I);
        const int32 Match = Body.FindBoneIndex(Name);
        if (Match == INDEX_NONE) { Reason = TEXT("unknown bone: ") + Name.ToString(); return false; }
        const int32 GP = Garment.GetParentIndex(I), BP = Body.GetParentIndex(Match);
        if ((GP == INDEX_NONE) != (BP == INDEX_NONE) ||
            (GP != INDEX_NONE && Garment.GetBoneName(GP) != Body.GetBoneName(BP)))
        { Reason = TEXT("different parent: ") + Name.ToString(); return false; }
        const FTransform& A = Garment.GetRefBonePose()[I];
        const FTransform& B = Body.GetRefBonePose()[Match];
        if (!A.GetTranslation().Equals(B.GetTranslation(), .1f) ||
            !A.GetScale3D().Equals(B.GetScale3D(), .001f) ||
            A.GetRotation().AngularDistance(B.GetRotation()) > FMath::DegreesToRadians(.5f))
        { Reason = TEXT("different rest pose: ") + Name.ToString(); return false; }
    }
    return true;
}

void ApplyAuraWardrobe(AActor* Character, USkeletalMeshComponent* Body)
{
    if (!Character || !Body || !Body->GetSkeletalMeshAsset() ||
        FParse::Param(FCommandLine::Get(), TEXT("AuraOriginalOutfit"))) return;
    TArray<FString> Paths;
    GConfig->GetArray(TEXT("Aura.Wardrobe"), TEXT("Garments"), Paths, GGameIni);
    if (Paths.IsEmpty()) return;
    if (Paths.Num() > 8) { UE_LOG(LogTemp, Warning, TEXT("Aura wardrobe: at most eight garment parts")); return; }
    TArray<USkeletalMesh*> Assets;
    for (const FString& Path : Paths)
    {
        USkeletalMesh* Mesh = Path.StartsWith(TEXT("/Game/")) ? LoadObject<USkeletalMesh>(nullptr, *Path, nullptr, LOAD_NoWarn) : nullptr;
        FString Reason;
        if (!Mesh || !IsAuraGarmentCompatible(Body->GetSkeletalMeshAsset()->GetRefSkeleton(), Mesh->GetRefSkeleton(), Reason))
        {
            UE_LOG(LogTemp, Warning, TEXT("Aura wardrobe: keeping preset; %s: %s"), *Path, Mesh ? *Reason : TEXT("missing local skeletal mesh"));
            return;
        }
        Assets.Add(Mesh);
    }
    // Validate every part before changing visibility of the assembled outfit.
    TArray<USkeletalMeshComponent*> Existing;
    Character->GetComponents(Existing);
    for (USkeletalMesh* Mesh : Assets)
    {
        USkeletalMeshComponent* Part = NewObject<USkeletalMeshComponent>(Character);
        Character->AddInstanceComponent(Part);
        Part->SetupAttachment(Body);
        Part->SetSkeletalMesh(Mesh);
        Part->SetLeaderPoseComponent(Body);
        Part->RegisterComponent();
    }
    for (USkeletalMeshComponent* Component : Existing)
    {
        // This is the assembled Ada outfit component, never Body or Face.
        if (Component->GetFName() == TEXT("SkeletalMesh")) Component->SetVisibility(false, false);
    }
    UE_LOG(LogTemp, Display, TEXT("Aura wardrobe: fitted %d garment parts"), Assets.Num());
}
