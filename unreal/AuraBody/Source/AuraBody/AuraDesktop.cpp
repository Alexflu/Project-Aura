#include "AuraDesktop.h"
#include "AuraRigActor.h"
#include "AuraMetaHuman.h"
#include "AuraPaths.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Widgets/SWindow.h"
#include "TextureResource.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformMisc.h"
#if PLATFORM_WINDOWS
#include "Windows/WindowsHWrapper.h"

struct FAuraDesktopNative
{
    HWND Window = nullptr;
    HDC DC = nullptr;
    HBITMAP Bitmap = nullptr;
    HGDIOBJ Previous = nullptr;
    uint8* Bytes = nullptr;
    static constexpr int Width = 480, Height = 720;
    static LRESULT CALLBACK Procedure(HWND Window, UINT Message, WPARAM W, LPARAM L)
    {
        if (Message == WM_NCHITTEST) return HTCAPTION;
        if (Message == WM_CLOSE || Message == WM_RBUTTONUP || Message == WM_NCRBUTTONUP)
        { FPlatformMisc::RequestExit(false); return 0; }
        return DefWindowProcW(Window, Message, W, L);
    }
    bool Open()
    {
        WNDCLASSW Class = {};
        Class.lpfnWndProc = Procedure;
        Class.hInstance = GetModuleHandleW(nullptr);
        Class.lpszClassName = L"AuraDesktopOverlay";
        Class.hCursor = LoadCursorW(nullptr, IDC_ARROW);
        RegisterClassW(&Class);
        RECT Work = {0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN)};
        SystemParametersInfoW(SPI_GETWORKAREA, 0, &Work, 0);
        Window = CreateWindowExW(WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
            Class.lpszClassName, L"Aura Desktop", WS_POPUP, Work.right - Width - 20,
            FMath::Max(Work.top, Work.bottom - Height), Width, Height, nullptr, nullptr, Class.hInstance, nullptr);
        DC = CreateCompatibleDC(nullptr);
        BITMAPINFO Info = {};
        Info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        Info.bmiHeader.biWidth = Width;
        Info.bmiHeader.biHeight = -Height;
        Info.bmiHeader.biPlanes = 1;
        Info.bmiHeader.biBitCount = 32;
        Info.bmiHeader.biCompression = BI_RGB;
        Bitmap = CreateDIBSection(DC, &Info, DIB_RGB_COLORS, reinterpret_cast<void**>(&Bytes), nullptr, 0);
        if (!Window || !DC || !Bitmap) return false;
        Previous = SelectObject(DC, Bitmap);
        return true;
    }
    ~FAuraDesktopNative()
    {
        if (DC && Previous) SelectObject(DC, Previous);
        if (Bitmap) DeleteObject(Bitmap);
        if (DC) DeleteDC(DC);
        if (Window) DestroyWindow(Window);
    }
};
#endif

UAuraDesktop::UAuraDesktop()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
    PrimaryComponentTick.TickInterval = 1.f / 30.f;
}

void UAuraDesktop::BeginPlay()
{
    Super::BeginPlay();
#if PLATFORM_WINDOWS
    Native = new FAuraDesktopNative;
    if (!Native->Open())
    { UE_LOG(LogTemp, Error, TEXT("Aura desktop window could not be created")); SetComponentTickEnabled(false); return; }
    Target = NewObject<UTextureRenderTarget2D>(this);
    Target->ClearColor = FLinearColor(0, 0, 0, 1);
    Target->InitCustomFormat(Native->Width, Native->Height, PF_FloatRGBA, false);
    Capture = NewObject<USceneCaptureComponent2D>(GetOwner());
    GetOwner()->AddInstanceComponent(Capture);
    Capture->bCaptureEveryFrame = false;
    Capture->bCaptureOnMovement = false;
    Capture->CaptureSource = SCS_SceneColorHDR;
    Capture->TextureTarget = Target;
    Capture->FOVAngle = 25;
    Capture->ShowFlags.SetAtmosphere(false);
    Capture->ShowFlags.SetFog(false);
    Capture->RegisterComponent();
#endif
}

void UAuraDesktop::TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(Dt, TickType, TickFunction);
#if PLATFORM_WINDOWS
    if (!Native || !Capture) return;
    const auto* Meta = GetOwner()->FindComponentByClass<UAuraMetaHuman>();
    if (!Meta || !Meta->bReady) return;
    const FVector Origin = GetOwner()->GetActorLocation();
    const FVector Position = Origin + FVector(330, 190, 130);
    Capture->SetWorldLocationAndRotation(Position, (Origin + FVector(0, 0, 90) - Position).Rotation());
    Capture->CaptureScene();
    FReadSurfaceDataFlags Flags(RCM_MinMax);
    Flags.SetLinearToGamma(false);
    if (!Target->GameThread_GetRenderTargetResource()->ReadLinearColorPixels(Pixels, Flags) || Pixels.Num() != Native->Width * Native->Height) return;
    int32 Opaque = 0, Clear = 0;
    for (int32 I = 0; I < Pixels.Num(); ++I)
    {
        const float Alpha = FMath::Clamp(1.f - Pixels[I].A, 0.f, 1.f);
        if (Alpha > .9f) ++Opaque;
        if (Alpha < .01f) ++Clear;
        // HDR scene capture stores inverse opacity. Convert to a premultiplied
        // BGRA overlay with a simple display curve; no color-key transparency.
        auto Channel = [Alpha](float Value)
        {
            const float Straight = FMath::Max(0.f, Value) / FMath::Max(Alpha, .001f);
            const float Mapped = Straight / (1.f + Straight);
            return static_cast<uint8>(FMath::Clamp(FMath::Pow(Mapped, 1.f / 2.2f) * Alpha * 255.f, 0.f, 255.f));
        };
        Native->Bytes[I * 4] = Channel(Pixels[I].B);
        Native->Bytes[I * 4 + 1] = Channel(Pixels[I].G);
        Native->Bytes[I * 4 + 2] = Channel(Pixels[I].R);
        Native->Bytes[I * 4 + 3] = static_cast<uint8>(Alpha * 255);
    }
    RECT Rect;
    GetWindowRect(Native->Window, &Rect);
    POINT Destination = {Rect.left, Rect.top}, Source = {0, 0};
    SIZE Size = {Native->Width, Native->Height};
    BLENDFUNCTION Blend = {AC_SRC_OVER, 0, 255, AC_SRC_ALPHA};
    if (!UpdateLayeredWindow(Native->Window, nullptr, &Destination, &Size, Native->DC, &Source, 0, &Blend, ULW_ALPHA)) return;
    ++PresentedFrames;
    if (!bPresented && Opaque > 100 && Clear > Pixels.Num() / 2)
    {
        ShowWindow(Native->Window, SW_SHOWNOACTIVATE);
        if (GEngine && GEngine->GameViewport && GEngine->GameViewport->GetWindow())
            GEngine->GameViewport->GetWindow()->HideWindow();
        bPresented = true;
        FFileHelper::SaveStringToFile(FString::Printf(TEXT("{\"opaque_pixels\":%d,\"clear_pixels\":%d,\"width\":480,\"height\":720}"), Opaque, Clear),
            *FPaths::Combine(AuraDataDirectory(), TEXT("desktop-ready.json")));
    }
    const double Now = FPlatformTime::Seconds();
    if (bPresented && Now - LastStatusAt >= 1)
    {
        LastStatusAt = Now;
        FFileHelper::SaveStringToFile(FString::Printf(TEXT("{\"presented_frames\":%d,\"opaque_pixels\":%d,\"clear_pixels\":%d}"), PresentedFrames, Opaque, Clear),
            *FPaths::Combine(AuraDataDirectory(), TEXT("desktop-status.json")));
    }
#endif
}

void UAuraDesktop::EndPlay(const EEndPlayReason::Type Reason)
{
#if PLATFORM_WINDOWS
    delete Native;
    Native = nullptr;
#endif
    Super::EndPlay(Reason);
}
