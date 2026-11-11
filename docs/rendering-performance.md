# Unreleased prop-rendering refinement

After beta 10 publication, prop rotation was restricted to the visible region and
interpolation padding. The original canvas pivot, placement and clipping remain
unchanged. Empty props skip rotation. This reduces the work spent on transparent
pixels without lowering the resolution or removing equipment animation.

A local comparison of 60 illustrated cast frames with four built-in items measured
47.82 ms mean / 51.17 ms p95 before, and 18.02 ms mean / 19.46 ms p95 afterward.
These are development-machine renderer timings, not a whole-application FPS
guarantee. Five before/after rendered frames had identical visible pixels.

114 tests pass. Additional comparisons cover off-center props, edge clipping,
square/non-square canvases, right-angle and arbitrary rotations, translucent art
over dark/light backgrounds, and empty input. Arbitrary-angle interpolation is
allowed a one-channel-value rounding tolerance. The live model-library window
check also passes. This refinement is not included in the beta 10 binary.
