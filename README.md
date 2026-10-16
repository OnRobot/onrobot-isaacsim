<p align="left">
  <img src="resource/onrobot-logo.png" alt="OnRobot" width="260">
</p>

# OnRobot grippers for Isaac Sim

Use 2FG7, 2FG14, RG2 and RG6 in an Isaac Sim 6.1 scene without ROS or
physical hardware. Each gripper includes geometry, materials, rigid-body
properties, joints and PhysX contact configuration in Asset Structure 3.0.

## Git LFS

This repository uses [Git LFS](https://git-lfs.com/) for large binary assets.
Install Git LFS before cloning and pull the LFS content after cloning:

```bash
git lfs install
git clone https://github.com/OnRobot/onrobot-isaacsim.git
cd onrobot-isaacsim
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
| 2FG7 | `assets/onrobot_2fg7/simready_usd/onrobot_2fg7.usda` | `finger_stroke` | metres |
| 2FG14 | `assets/onrobot_2fg14/simready_usd/onrobot_2fg14.usda` | `finger_stroke` | metres |
| RG2 | `assets/onrobot_rg2/simready_usd/onrobot_rg2.usda` | `finger_joint` | radians |
| RG6 | `assets/onrobot_rg6/simready_usd/onrobot_rg6.usda` | `finger_joint` | radians |

Keep each `assets/onrobot_<model>/` directory together. Open its
`simready_usd/onrobot_<model>.usda` entry point in Isaac Sim, ROS
applications or other compatible tools. It references the adjacent
`payloads/` layers. Metadata and thumbnails travel with the same model;
no external model download is needed. Your application scene supplies
lighting, cameras and a PhysicsScene.
The selected PhysX variant includes the joint linkage and fingertip contact.
Do not control the mimic joints independently.

To add a gripper to an existing scene, reference its default prim under your
chosen prim path. For example, in Isaac's Script Editor:

```python
import omni.usd

stage = omni.usd.get_context().get_stage()
gripper = stage.DefinePrim('/World/Gripper', 'Xform')
gripper.GetReferences().AddReference(
    '/path/to/onrobot-isaacsim/assets/onrobot_2fg7/simready_usd/onrobot_2fg7.usda')
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

With Isaac Sim installed, also load each USD with its referenced layers and
check that they work together:

```bash
/path/to/isaac-sim/python.sh tools/validate_assets.py
```

Both checks report `"status": "passed"` on success. The composed-stage check
also lists all four models.
This verifies file integrity, metre units, default prims, articulation roots
and driven joints. It is not a gripping-force or payload certification.

## Contact and application settings

The aluminum housings and metal finger parts use the same gray satin material.
Labels, rubber and colored details keep their own materials. The aluminum uses
`UsdPreviewSurface` to approximate the finish; it does not reproduce a measured
brushed-metal surface or its directional reflections.
Appearance depends on your scene lighting. Editing the visual material does
not change fingertip friction, which uses separate physics-purpose bindings.

The standard pads use static friction **0.6**, dynamic friction **0.5** and
average friction combining. These are plausible rubber/metal assumptions,
not measurements for every workpiece. Object materials, finger geometry,
the difference between target and actual joint position, drive limits and
acceleration all affect whether the gripper holds the object.
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

This setting helps keep contact stable under load without increasing friction
or grip effort. Set it in your application scene; adding a gripper does not
change the scene's physics settings. Test whether the gripper holds the object
and whether the result changes with the timestep. The supplied showcase runners
configure this setting automatically. When mounting a gripper into a larger
articulation, use these solver settings on the combined articulation root:
at least 64 position iterations, and no more
than four velocity iterations for TGS.

The 2FG position drives include provisional inertia and damping settings to
keep both loaded contact and free motion stable. They change how the joints
respond to forces without increasing the gripper's gravitational mass. These
are simulation settings, not measured motor parameters or a reproduction of
the firmware's motion timing.

The assets have been exercised with a rigid 62 mm cube weighing 0.712 kg in
table pickup, lift, pendulum motion, setdown and release on Isaac Sim 6.1.
That demonstration does not establish force accuracy or the timing of a real
gripper. Test the mass, materials and motion in your application before relying
on the simulation's grasp results.

## ROS integration

`onrobot_gripper_isaac` in the
[OnRobot ROS 2 repository](https://github.com/OnRobot/onrobot-ros2)
installs a matching
copy of these assets with its controllers, bridge and demonstration runners.
It uses the minimum SimReady package versions and interface revisions declared
by the ROS package, and verifies the file checksums. Compatible asset updates
do not require a ROS release; rebuild `onrobot_gripper_isaac` to install them.
No ROS package or build is required for the standalone assets above.

## Asset versions and compatibility

Each model's `com.nvidia.simready.packaging.json` contains a `package_id`
ending in `YYYY.MM.DD_revision`, for example `2026.10.07_01`. This is the asset
package version; the final revision is compared numerically. Changed package
contents receive a new version. The root `asset_manifest.json` records the
same identity, all package file hashes and an `interface_revision` per model.

Interface revision **1** preserves the entry point, default prim, articulation
root, physical joint names, units, axes, limits and linkage used by applications.
Compatible material, contact and drive tuning can keep this revision. Changes
to those paths or kinematics require a new interface revision and an application
update. `asset_structure_version` describes the USD layout convention; NVIDIA
`format_version` describes its metadata format. Neither is an asset release
version. Retest application behavior when updating physics or contact tuning.

Supplied under the [BSD 3-Clause License](LICENSE).
