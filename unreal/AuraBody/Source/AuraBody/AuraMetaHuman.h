#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Components/ActorComponent.h"
#include "AuraMetaHuman.generated.h"

class UAuraBehaviorComponent;
class USkinnedMeshComponent;
class USkeletalMeshComponent;

// Game-thread inputs are copied into the proxy before animation worker evaluation.
UCLASS(Transient)
class AURABODY_API UAuraMetaHumanAnim : public UAnimInstance
{
    GENERATED_BODY()
public:
    UPROPERTY(Transient) TObjectPtr<USkinnedMeshComponent> PoseSource;
    UPROPERTY(Transient) TObjectPtr<UAuraBehaviorComponent> Behavior;
    bool bFace = false;
    double PoseUpdateUs = 0;
    int32 RetargetCacheBuilds = 0;
protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) override;
};

UCLASS()
class AURABODY_API UAuraMetaHuman : public UActorComponent
{
    GENERATED_BODY()
public:
    UAuraMetaHuman();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    UPROPERTY(Transient) TObjectPtr<AActor> Character;
    UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> Body;
    UPROPERTY(Transient) TObjectPtr<USkeletalMeshComponent> Face;
    bool bReady = false;
private:
    double StartedAt = 0;
    double LastSample = 0;
    FString TelemetryPath;
};
