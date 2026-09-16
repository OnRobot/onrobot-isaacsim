<p align="left">
  <img src="resource/onrobot-logo.png" alt="OnRobot" width="260">
</p>

# OnRobot grippers for Isaac Sim

Use 2FG7, 2FG14, RG2 and RG6 in an Isaac Sim 6.0.1 scene without ROS or
physical hardware. Each gripper includes geometry, materials, rigid-body
properties, joints and PhysX contact configuration in Asset Structure 3.0.

## Git LFS

This repository uses [Git LFS](https://git-lfs.com/) for large binary assets.
Install Git LFS before cloning and pull the LFS content after cloning:

```bash
git lfs install
git clone https://github.com/OnRobot/onrobot-isaacsim.git
cd onrobot-isaac-sim
git lfs pull
```

If the repository is already cloned, install Git LFS and fetch the content from
the repository root:

```bash
git lfs install
git lfs pull
```

## Open a gripper

In Isaac Sim, select **File → Open** and choose an entry point:

| Model | Entry point | Driven joint | Coordinate |
|---|---|---|---|
| 2FG7 | `assets/2fg7/onrobot_2fg7.usda` | `finger_stroke` | metres |
| 2FG14 | `assets/2fg14/onrobot_2fg14.usda` | `finger_stroke` | metres |
| RG2 | `assets/rg2/onrobot_rg2.usda` | `finger_joint` | radians |
| RG6 | `assets/rg6/onrobot_rg6.usda` | `finger_joint` | radians |

Keep the model's entire directory together. The entry point references its
`payloads/` layers using relative paths. No external model download is needed.
The selected PhysX variant includes the joint linkage and fingertip contact.
Do not control the mimic joints independently.

To add a gripper to an existing scene, reference its default prim under your
chosen prim path. For example, in Isaac's Script Editor:

```python
import omni.usd

stage = omni.usd.get_context().get_stage()
gripper = stage.DefinePrim('/World/Gripper', 'Xform')
gripper.GetReferences().AddReference(
    '/path/to/onrobot-isaac-sim/assets/2fg7/onrobot_2fg7.usda')
```

Configure your scene's gravity, timestep and collision objects before playing.
The supplied grippers have a fixed base. Mounting to a moving articulation
requires replacing the fixed-to-world connection with the intended mount;
moving an ancestor transform alone is not a physical robot attachment.

The physical joint coordinate is not the distance between the fingertip
surfaces. Account for the installed finger geometry when converting a task
aperture into a joint target. The ROS integration provides this conversion.
The table uses Isaac articulation API units. When editing USD angular joint
limits or angular-drive targets directly, use degrees instead of radians.

## Verify the files

From this repository, use ordinary Python to check all asset checksums:

```bash
python3 tools/validate_assets.py --manifest-only
```

With Isaac Sim installed, also check composed stages and their dependencies:

```bash
/path/to/isaac-sim/python.sh tools/validate_assets.py
```

A successful report lists all four models and `"status": "passed"`.
This verifies file integrity, metre units, default prims, articulation roots
and driven joints. It is not a gripping-force or payload certification.

## Contact and application settings

The aluminum housings and metal finger parts use a shared gray satin visual
material; labels, rubber and colored details keep their own materials. This is a portable
`UsdPreviewSurface` approximation, not a measured directional brushed finish.
Appearance depends on your scene lighting. Editing the visual material does
not change fingertip friction, which uses separate physics-purpose bindings.

The standard pads use static friction **0.6**, dynamic friction **0.5** and
average friction combining. These are plausible rubber/metal assumptions,
not measurements for every workpiece. Object materials, finger geometry,
commanded joint error, drive limits and acceleration all affect retention.
Keep requested force, joint drive effort and measured contact force distinct.

For loaded grasps, configure the **existing scene** before starting physics:
use the TGS solver, a timestep of 1/480 s or finer, and enable external forces
at every TGS iteration. In Isaac's Script Editor, substitute your scene path:

```python
import omni.usd
from pxr import PhysxSchema, UsdPhysics

stage = omni.usd.get_context().get_stage()
scene = UsdPhysics.Scene.Get(stage, '/World/PhysicsScene')
if not scene:
    raise RuntimeError('Use the path of your existing PhysicsScene')
physics = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
physics.CreateSolverTypeAttr().Set('TGS')
physics.CreateTimeStepsPerSecondAttr().Set(480)
physics.CreateEnableExternalForcesEveryIterationAttr().Set(True)
```

This scene-level setting improves loaded-contact stability without increasing
friction or grip effort. It is deliberately not imposed by a gripper reference
on the rest of your application. Confirm retention and timestep sensitivity in
your complete scene; the supplied showcase runners configure it automatically.
When mounting a gripper into a larger articulation, preserve its solver policy
on the combined articulation root: at least 64 position iterations, and no more
than four velocity iterations for TGS.

The 2FG position drives include provisional reflected-inertia and matched-damping
settings to keep both loaded contact and free motion stable. They add joint-space
inertia, not gravitational mass. They are numerical servo-model assumptions,
not measured motor parameters or a model of the firmware's motion timing.

The assets have been exercised with a rigid 62 mm cube weighing 0.712 kg in
table pickup, lift, pendulum motion, setdown and release on Isaac Sim 6.0.1.
Do not interpret that demonstration as calibrated force, hardware-equivalent
timing or guaranteed retention for every rated-load fixture. Validate your
application's mass, material pair and motion.

## ROS integration

`onrobot_gripper_isaac` in the OnRobot ROS 2 repository installs a matching
copy of these assets with its controllers, bridge and demonstration runners.
It consumes this repository's content manifest rather than maintaining a
second source copy. No ROS package or build is required for the standalone
assets above.

Supplied under the [BSD 3-Clause License](LICENSE).
