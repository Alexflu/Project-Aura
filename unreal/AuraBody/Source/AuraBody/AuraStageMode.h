#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "AuraStageMode.generated.h"

UCLASS()
class AURABODY_API AAuraStageMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AAuraStageMode();
    virtual void BeginPlay() override;
};

UCLASS()
class AURABODY_API AAuraStageHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
private:
    double TotalSeconds = 0;
    double WorstSeconds = 0;
    int32 Frames = 0;
};
