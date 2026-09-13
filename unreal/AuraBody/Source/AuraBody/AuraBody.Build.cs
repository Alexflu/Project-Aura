using UnrealBuildTool;
public class AuraBody : ModuleRules
{
    public AuraBody(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new string[] { "Json", "SlateCore", "RenderCore", "RHI" });
        if (Target.Platform == UnrealTargetPlatform.Win64)
            PublicSystemLibraries.AddRange(new string[] { "user32.lib", "gdi32.lib" });
    }
}
