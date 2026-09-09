using UnrealBuildTool;
using System.Collections.Generic;
public class AuraBodyTarget : TargetRules
{
    public AuraBodyTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("AuraBody");
    }
}
