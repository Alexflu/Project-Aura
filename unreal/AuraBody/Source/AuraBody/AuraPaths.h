#pragma once
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"

// Startup configuration only; semantic input cannot select files or directories.
inline FString AuraDataDirectory()
{
    FString Directory;
    if (FParse::Value(FCommandLine::Get(), TEXT("AuraDataDir="), Directory))
        return FPaths::ConvertRelativePathToFull(Directory);
    return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Aura"));
}
