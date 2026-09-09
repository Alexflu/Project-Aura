#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AuraBehaviorComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FAuraBehaviorUpdated);

// A renderer input only. Blueprint owns skeleton/animation binding.
UCLASS(ClassGroup=(Aura), meta=(BlueprintSpawnableComponent))
class AURABODY_API UAuraBehaviorComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UAuraBehaviorComponent();
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(BlueprintReadOnly, Category="Aura") FString Mode = TEXT("idle");
    UPROPERTY(BlueprintReadOnly, Category="Aura") FString Gesture = TEXT("none");
    UPROPERTY(BlueprintReadOnly, Category="Aura") FVector PositionCm = FVector::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Aura") FVector GazeTargetCm = FVector(200, 0, 160);
    UPROPERTY(BlueprintReadOnly, Category="Aura") float MouthOpen = 0;
    UPROPERTY(BlueprintReadOnly, Category="Aura") bool bMoving = false;
    UPROPERTY(BlueprintReadOnly, Category="Aura") bool bPaused = false;
    UPROPERTY(BlueprintReadOnly, Category="Aura") bool bConnected = false;
    UPROPERTY(BlueprintReadOnly, Category="Aura") FString LastError = TEXT("Waiting for producer");

    // Fired only for a new validated state or a transition to disconnected.
    UPROPERTY(BlueprintAssignable, Category="Aura") FAuraBehaviorUpdated OnBehaviorUpdated;

private:
    FString LastSession;
    double LastSequence = -1;
    double LastFreshTime = 0;
    void Disconnect(const FString& Reason);
};
