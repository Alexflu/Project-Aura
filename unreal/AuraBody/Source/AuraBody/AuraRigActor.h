#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AuraRigActor.generated.h"

class UAuraBehaviorComponent;
class UPoseableMeshComponent;
class USkeletalMesh;

// Disposable mannequin harness. The semantic receiver is independent of this rig.
UCLASS(Config=Game)
class AURABODY_API AAuraRigActor : public AActor
{
    GENERATED_BODY()
public:
    AAuraRigActor();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    FVector2D GetEyeGazeDegrees() const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UAuraBehaviorComponent> Behavior;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UPoseableMeshComponent> Body;
    UPROPERTY(Config, EditAnywhere, Category="Aura") FString SkeletalMeshPath = TEXT("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple");
    UPROPERTY(BlueprintReadOnly) bool bRigReady = false;
    UPROPERTY(BlueprintReadOnly) FString RigError;
    UPROPERTY(BlueprintReadOnly) int32 BoneCount = 0;

private:
    FVector StageOrigin;
    float MotionTime = 0;
    float WalkWeight = 0;
    float WaveWeight = 0;
    float NodWeight = 0;
    float NodTime = 0;
    float AttentiveWeight = 0;
    bool bWasNodding = false;
    float GazeYaw = 0;
    float GazePitch = 0;
    TArray<FTransform> ReferenceLocal;
    TArray<FTransform> Pose;
    TArray<FName> BoneNames;
    TArray<int32> Parents;
    void UpdatePose(float DeltaSeconds);
    bool bTelemetry = false;
    double StartedAt = 0;
    double LastSample = 0;
    double LastFrameAt = 0;
    double FrameIntervalTotal = 0;
    double FrameIntervalWorst = 0;
    int32 MeasuredFrames = 0;
    int32 FramesOver50Ms = 0;
    FString TelemetryPath;
    void RecordSample(float DeltaSeconds);
};
