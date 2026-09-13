#pragma once
#include "CoreMinimal.h"

class AActor;
class USkeletalMeshComponent;
struct FReferenceSkeleton;

bool IsAuraGarmentCompatible(const FReferenceSkeleton& Body, const FReferenceSkeleton& Garment, FString& Reason);
void ApplyAuraWardrobe(AActor* Character, USkeletalMeshComponent* Body);
