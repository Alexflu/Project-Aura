#include "AuraStageMode.h"
#include "AuraRigActor.h"
#include "AuraMetaHuman.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "AuraBehaviorComponent.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Canvas.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/SkyLight.h"
#include "Engine/PointLight.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"

AAuraStageMode::AAuraStageMode()
{
    DefaultPawnClass = nullptr;
    HUDClass = AAuraStageHUD::StaticClass();
}

void AAuraStageMode::BeginPlay()
{
    Super::BeginPlay();
    UWorld* World = GetWorld();
    AAuraRigActor* Driver = World->SpawnActor<AAuraRigActor>(FVector::ZeroVector, FRotator::ZeroRotator);
    if (FParse::Param(FCommandLine::Get(), TEXT("AuraMetaHuman")))
    {
        UAuraMetaHuman* Adapter = NewObject<UAuraMetaHuman>(Driver);
        Driver->AddInstanceComponent(Adapter);
        Adapter->RegisterComponent();
    }
    AStaticMeshActor* Floor = World->SpawnActor<AStaticMeshActor>(FVector(0, 0, -5), FRotator::ZeroRotator);
    Floor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
    Floor->GetStaticMeshComponent()->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
    Floor->SetActorScale3D(FVector(12, 12, .1f));
    ADirectionalLight* Light = World->SpawnActor<ADirectionalLight>(FVector(100, -100, 400), FRotator(-45, -30, 0));
    Light->GetLightComponent()->SetIntensity(4);
    ASkyLight* Fill = World->SpawnActor<ASkyLight>();
    Fill->GetLightComponent()->SetIntensity(1);
    APointLight* Front = World->SpawnActor<APointLight>(FVector(250, -300, 230), FRotator::ZeroRotator);
    Front->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    Front->GetLightComponent()->SetIntensity(16000);
    Front->PointLightComponent->SetAttenuationRadius(1000);
    ACameraActor* Camera = World->SpawnActor<ACameraActor>();
    // Present the face from the same side as the authored gaze target.
    const FVector CameraPosition(600, 350, 210);
    Camera->SetActorLocation(CameraPosition);
    Camera->SetActorRotation((FVector(60, 0, 95) - CameraPosition).Rotation());
    Camera->GetCameraComponent()->SetFieldOfView(40);
    if (APlayerController* Player = UGameplayStatics::GetPlayerController(World, 0))
        Player->SetViewTarget(Camera);
}

void AAuraStageHUD::DrawHUD()
{
    Super::DrawHUD();
    if (!Canvas) return;
    AAuraRigActor* Rig = nullptr;
    for (TActorIterator<AAuraRigActor> It(GetWorld()); It; ++It) { Rig = *It; break; }
    DrawRect(FLinearColor(.015, .025, .04, .9), 16, 16, 510, 165);
    DrawText(TEXT("AURA / SKELETON ZERO"), FLinearColor(.4, .85, 1), 30, 25, nullptr, 1.5f);
    DrawText(TEXT("REAL SKELETAL MESH / AUTHORED OFFLINE CUES / NO LIVE AI"), FLinearColor::White, 30, 55);
    if (!Rig) return;
    const UAuraMetaHuman* MetaHuman = Rig->FindComponentByClass<UAuraMetaHuman>();
    const UAuraBehaviorComponent* State = Rig->Behavior;
    const FString Status = FString::Printf(TEXT("%s | %s | %s | %d bones"),
        State->bConnected ? (State->bPaused ? TEXT("PAUSED") : TEXT("CONNECTED")) : TEXT("WAITING"),
        *State->Mode, *State->Gesture, Rig->BoneCount);
    DrawText(MetaHuman && MetaHuman->bReady ? Status + TEXT(" / MetaHuman body + face") : Status, FLinearColor::White, 30, 80);
    DrawText(Rig->bRigReady ? State->LastError : Rig->RigError, FLinearColor(1, .6, .4), 30, 103);
    DrawText(FString::Printf(TEXT("Expression: %s %.2f | Posture: %s | Blush: %.2f"),
        *State->Expression, State->ExpressionIntensity, *State->Posture, State->Blush), FLinearColor::White, 30, 125);
    DrawText(MetaHuman && MetaHuman->bReady ? TEXT("MetaHuman jaw control / synthetic cue / no audio") : TEXT("Synthetic mouth cue (mannequin has no facial rig)"), FLinearColor::White, 30, 148);
    DrawRect(FLinearColor(.1, .15, .2), 340, 150, 150, 12);
    DrawRect(FLinearColor(.3, .9, .8), 340, 150, 150 * State->MouthOpen, 12);
    const double Dt = FApp::GetDeltaTime();
    TotalSeconds += Dt;
    WorstSeconds = FMath::Max(WorstSeconds, Dt);
    ++Frames;
    DrawText(FString::Printf(TEXT("Frame %.1f ms | mean %.1f ms | worst %.1f ms"),
        Dt * 1000, TotalSeconds / Frames * 1000, WorstSeconds * 1000), FLinearColor::White, 30, Canvas->ClipY - 35);
}
