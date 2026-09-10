using UnrealBuildTool;
using System.Collections.Generic;
public class AuraBodyEditorTarget : TargetRules
{
    public AuraBodyEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("AuraBody");
    }
}
