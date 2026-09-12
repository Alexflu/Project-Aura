#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AuraDesktop.generated.h"

class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
struct FAuraDesktopNative;

UCLASS()
class AURABODY_API UAuraDesktop : public UActorComponent
{
    GENERATED_BODY()
public:
    UAuraDesktop();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
private:
    UPROPERTY(Transient) TObjectPtr<USceneCaptureComponent2D> Capture;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> Target;
    FAuraDesktopNative* Native = nullptr;
    TArray<FLinearColor> Pixels;
    bool bPresented = false;
    double LastStatusAt = 0;
    int32 PresentedFrames = 0;
};
