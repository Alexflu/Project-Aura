#include "AuraBehaviorComponent.h"
#include "AuraPaths.h"
#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

UAuraBehaviorComponent::UAuraBehaviorComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 1.0f / 30.0f;
}

void UAuraBehaviorComponent::Disconnect(const FString& Reason)
{
    LastError = Reason;
    if (!bConnected) return;
    bConnected = false;
    Mode = TEXT("idle");
    Gesture = TEXT("none");
    Expression = TEXT("neutral");
    ExpressionIntensity = 0;
    Posture = TEXT("neutral");
    Blush = 0;
    MouthOpen = 0;
    bMoving = false;
    bPaused = true;
    // Hold position; never snap the character home on lost input.
    OnBehaviorUpdated.Broadcast();
}

void UAuraBehaviorComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    const double Now = FPlatformTime::Seconds();
    const FString Path = FPaths::Combine(AuraDataDirectory(), TEXT("behavior.json"));
    auto Fail = [this, Now](const FString& Reason)
    {
        LastError = Reason;
        if (Now - LastFreshTime > 1.0) Disconnect(Reason);
    };
    const int64 Size = IFileManager::Get().FileSize(*Path);
    if (Size <= 0 || Size > 4096) { Fail(TEXT("Missing or oversized snapshot")); return; }
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *Path) || Text.Len() > 4096)
    { Fail(TEXT("Snapshot read failed")); return; }
    TSharedPtr<FJsonObject> Object;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Object) || !Object.IsValid())
    { Fail(TEXT("Invalid JSON")); return; }
    auto Num = [&Object](const TCHAR* Key, double& Value, double Low, double High)
    {
        return Object->TryGetNumberField(Key, Value) && FMath::IsFinite(Value)
            && Value >= Low && Value <= High;
    };
    double Version, Sequence, X, Y, GX, GY, GZ, Mouth, NewExpressionIntensity, NewBlush;
    FString Session, NewMode, NewGesture, NewExpression, NewPosture;
    bool Paused, Moving;
    if (Object->Values.Num() != 17 ||
        !Num(TEXT("version"), Version, 1, 1) ||
        !Num(TEXT("sequence"), Sequence, 1, 9007199254740991.0) ||
        Sequence != FMath::FloorToDouble(Sequence) ||
        !Num(TEXT("x"), X, -500, 500) || !Num(TEXT("y"), Y, -500, 500) ||
        !Num(TEXT("gaze_x"), GX, -500, 500) || !Num(TEXT("gaze_y"), GY, -500, 500) ||
        !Num(TEXT("gaze_z"), GZ, -500, 500) || !Num(TEXT("mouth_open"), Mouth, 0, 1) ||
        !Num(TEXT("expression_intensity"), NewExpressionIntensity, 0, 1) ||
        !Num(TEXT("blush"), NewBlush, 0, 1) ||
        !Object->TryGetStringField(TEXT("session"), Session) || Session.Len() != 36 ||
        !Object->TryGetStringField(TEXT("mode"), NewMode) ||
        !(NewMode == TEXT("idle") || NewMode == TEXT("listening") || NewMode == TEXT("speaking")) ||
        !Object->TryGetStringField(TEXT("gesture"), NewGesture) ||
        !(NewGesture == TEXT("none") || NewGesture == TEXT("wave") || NewGesture == TEXT("nod")) ||
        !Object->TryGetStringField(TEXT("expression"), NewExpression) ||
        !(NewExpression == TEXT("neutral") || NewExpression == TEXT("happy") ||
          NewExpression == TEXT("curious") || NewExpression == TEXT("concerned")) ||
        !Object->TryGetStringField(TEXT("posture"), NewPosture) ||
        !(NewPosture == TEXT("neutral") || NewPosture == TEXT("attentive") || NewPosture == TEXT("relaxed")) ||
        !Object->TryGetBoolField(TEXT("paused"), Paused) ||
        !Object->TryGetBoolField(TEXT("moving"), Moving))
    { Fail(TEXT("Unsupported snapshot fields")); return; }

    // First observation only primes the stream. A static leftover file cannot animate.
    if (Session != LastSession)
    {
        Disconnect(TEXT("New producer session; waiting for advancing sequence"));
        LastSession = Session;
        LastSequence = Sequence;
        return;
    }
    if (Sequence <= LastSequence)
    { Fail(TEXT("Waiting for advancing sequence")); return; }
    LastSequence = Sequence;
    LastFreshTime = Now;
    bConnected = true;
    LastError.Empty();
    bPaused = Paused;
    Mode = Paused ? TEXT("idle") : NewMode;
    Gesture = Paused ? TEXT("none") : NewGesture;
    Expression = NewExpression;
    ExpressionIntensity = NewExpressionIntensity;
    Posture = NewPosture;
    Blush = NewBlush;
    PositionCm = FVector(X, Y, 0);
    GazeTargetCm = FVector(GX, GY, GZ);
    MouthOpen = !Paused && NewMode == TEXT("speaking") ? Mouth : 0;
    bMoving = !Paused && Moving;
    OnBehaviorUpdated.Broadcast();
}
