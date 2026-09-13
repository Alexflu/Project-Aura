#if WITH_DEV_AUTOMATION_TESTS
#include "AuraWardrobe.h"
#include "ReferenceSkeleton.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAuraWardrobeRigTest, "Aura.Wardrobe.RigCompatibility",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FAuraWardrobeRigTest::RunTest(const FString& Parameters)
{
    auto Skeleton = [](FName Child, FVector Offset, bool Reparent)
    {
        FReferenceSkeleton Result;
        FReferenceSkeletonModifier Edit(Result, nullptr);
        Edit.Add(FMeshBoneInfo(TEXT("root"), TEXT("root"), INDEX_NONE), FTransform::Identity);
        Edit.Add(FMeshBoneInfo(TEXT("pelvis"), TEXT("pelvis"), 0), FTransform(FVector(0, 0, 90)));
        Edit.Add(FMeshBoneInfo(Child, Child.ToString(), Reparent ? 0 : 1), FTransform(Offset));
        return Result;
    };
    const FReferenceSkeleton Body = Skeleton(TEXT("spine"), FVector(0, 0, 10), false);
    FString Reason;
    TestTrue(TEXT("Exact fitted rig accepted"), IsAuraGarmentCompatible(Body, Body, Reason));
    TestFalse(TEXT("Foreign rig rejected"), IsAuraGarmentCompatible(Body, Skeleton(TEXT("foreign"), FVector(0,0,10), false), Reason));
    TestFalse(TEXT("Different body proportions rejected"), IsAuraGarmentCompatible(Body, Skeleton(TEXT("spine"), FVector(0,0,20), false), Reason));
    TestFalse(TEXT("Reparented bone rejected"), IsAuraGarmentCompatible(Body, Skeleton(TEXT("spine"), FVector(0,0,10), true), Reason));
    TestFalse(TEXT("Empty rig rejected"), IsAuraGarmentCompatible(Body, FReferenceSkeleton(), Reason));
    return true;
}
#endif
