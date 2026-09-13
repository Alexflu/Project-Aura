#include "AuraAppearance.h"
#include "Components/MeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GroomComponent.h"
#include "GroomAsset.h"
#include "GroomBindingAsset.h"
#if WITH_EDITOR
#include "GroomBindingCompiler.h"
#endif
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

void ApplyAuraAppearance(AActor* Character)
{
    if (!Character) return;
    if (!FParse::Param(FCommandLine::Get(), TEXT("AuraOriginalHair")))
    {
        UGroomComponent* Hair = nullptr;
        USkeletalMeshComponent* Face = nullptr;
        TArray<UActorComponent*> Components;
        Character->GetComponents(Components);
        for (UActorComponent* Component : Components)
        {
            if (Component->GetFName() == TEXT("Hair")) Hair = Cast<UGroomComponent>(Component);
            if (Component->GetFName() == TEXT("Face")) Face = Cast<USkeletalMeshComponent>(Component);
        }
        // Local prepared assets are optional. Keep the assembled groom on failure.
        UGroomAsset* Groom = LoadObject<UGroomAsset>(nullptr, TEXT("/Game/Aura/Appearance/Hair_M_Layered.Hair_M_Layered"), nullptr, LOAD_NoWarn);
        UGroomBindingAsset* Binding = LoadObject<UGroomBindingAsset>(nullptr, TEXT("/Game/Aura/Appearance/Hair_M_Layered_Binding.Hair_M_Layered_Binding"), nullptr, LOAD_NoWarn);
#if WITH_EDITOR
        // Editor game startup may still be building the newly loaded binding.
        if (Binding) FGroomBindingCompilingManager::Get().FinishCompilation({Binding});
#endif
        if (Hair && Face && Groom && Binding &&
            UGroomBindingAsset::IsCompatible(Face->GetSkeletalMeshAsset(), Binding, true) &&
            UGroomBindingAsset::IsCompatible(Groom, Binding, true))
        {
            Hair->SetGroomAsset(Groom, Binding);
            UE_LOG(LogTemp, Display, TEXT("Aura appearance: layered hair bound to face"));
        }
        else UE_LOG(LogTemp, Display, TEXT("Aura appearance: keeping assembled hair; prepare local layered assets to enable replacement"));
    }
    if (FParse::Param(FCommandLine::Get(), TEXT("AuraOriginalMaterials"))) return;
    TArray<UMeshComponent*> Meshes;
    Character->GetComponents(Meshes);
    int32 Changed = 0;
    for (UMeshComponent* Mesh : Meshes)
    {
        for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
        {
            UMaterialInterface* Source = Mesh->GetMaterial(Slot);
            if (!Source) continue;
            const bool Hair = Mesh->GetFName() == TEXT("Hair");
            const bool Eye = Mesh->GetFName() == TEXT("Face") &&
                (Source->GetName().Contains(TEXT("MI_EyeL_Baked")) || Source->GetName().Contains(TEXT("MI_EyeR_Baked")));
            const bool Clothing = Source->GetPathName().Contains(TEXT("/Clothing/"));
            if (!Hair && !Eye && !Clothing) continue;
            UMaterialInstanceDynamic* Material = Mesh->CreateDynamicMaterialInstance(Slot, Source);
            if (!Material) continue;
            auto Vector = [Material](const TCHAR* Name, FLinearColor Value)
            {
                FLinearColor Existing;
                if (Material->GetVectorParameterValue(FMaterialParameterInfo(Name), Existing))
                    Material->SetVectorParameterValue(Name, Value);
                else UE_LOG(LogTemp, Warning, TEXT("Aura appearance: missing vector %s"), Name);
            };
            auto Scalar = [Material](const TCHAR* Name, float Value)
            {
                float Existing;
                if (Material->GetScalarParameterValue(FMaterialParameterInfo(Name), Existing))
                    Material->SetScalarParameterValue(Name, Value);
                else UE_LOG(LogTemp, Warning, TEXT("Aura appearance: missing scalar %s"), Name);
            };
            if (Hair)
            {
                // Restrained violet dye; the final layered groom needs its own tip mask.
                Vector(TEXT("hairDye"), FLinearColor(.012f, .008f, .02f));
                Scalar(TEXT("hairMelanin"), .15f);
                Scalar(TEXT("Ombre"), 1.f);
                Scalar(TEXT("OmbreShift"), .45f);
                Scalar(TEXT("OmbreContrast"), 2.f);
                Scalar(TEXT("OmbreIntensity"), .35f);
                Scalar(TEXT("OmbreMelanin"), 0.f);
                Vector(TEXT("OmbrehairDye"), FLinearColor(.06f, .008f, .14f));
            }
            else if (Eye)
            {
                Vector(TEXT("Iris Color Multiply"), FLinearColor(.55f, .18f, 1.f));
            }
            else
            {
                Vector(TEXT("diffuse_color_1"), FLinearColor(.018f, .015f, .025f));
                Vector(TEXT("diffuse_color_2"), FLinearColor(.045f, .03f, .06f));
                Vector(TEXT("B_diffuse_color_1"), FLinearColor(.16f, .025f, .32f));
            }
            ++Changed;
        }
    }
    UE_LOG(LogTemp, Display, TEXT("Aura appearance: palette applied to %d material slots"), Changed);
}
