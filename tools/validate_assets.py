#!/usr/bin/env python3
"""Check a portable OnRobot asset tree, optionally composing its USD stages."""

import argparse
import hashlib
import json
from pathlib import Path


def verify_manifest(root):
    root = Path(root).resolve()
    if (root / 'assets').is_symlink() or (root / 'asset_manifest.json').is_symlink():
        raise ValueError('asset directory and manifest must not be symlinks')
    manifest = json.loads((root / 'asset_manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1 or not manifest.get('files'):
        raise ValueError('unsupported or empty asset manifest')
    actual = set()
    for path in (root / 'assets').rglob('*'):
        if path.is_symlink():
            raise ValueError(f'asset symlinks are not portable: {path}')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != set(manifest['files']):
        raise ValueError('asset file set differs from the manifest')
    for relative, expected in manifest['files'].items():
        path = root / relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'asset checksum mismatch: {relative}')
    return manifest


def validate(root, *, manifest_only=False):
    root = Path(root).resolve()
    manifest = verify_manifest(root)
    report = {'status': 'passed', 'file_count': len(manifest['files']),
              'composition_checked': not manifest_only, 'models': {}}
    if manifest_only:
        return report
    if set(manifest.get('models', {})) != {'2fg7', '2fg14', 'rg2', 'rg6'}:
        raise ValueError('the composed-stage check requires all four model entries')
    from pxr import Usd, UsdGeom, UsdPhysics, UsdUtils
    for model, info in manifest['models'].items():
        entry = root / info['entrypoint']
        layers, dependencies, unresolved = UsdUtils.ComputeAllDependencies(str(entry))
        if unresolved:
            raise ValueError(f'{model}: unresolved dependencies: {unresolved}')
        for dependency in [layer.realPath for layer in layers] + list(dependencies):
            if dependency and not Path(dependency).resolve().is_relative_to(root):
                raise ValueError(f'{model}: external dependency: {dependency}')
        stage = Usd.Stage.Open(str(entry), load=Usd.Stage.LoadAll)
        if not stage or stage.GetCompositionErrors():
            raise ValueError(f'{model}: USD composition failed')
        if str(stage.GetDefaultPrim().GetPath()) != info['default_prim']:
            raise ValueError(f'{model}: unexpected default prim')
        if UsdGeom.GetStageMetersPerUnit(stage) != 1.0:
            raise ValueError(f'{model}: expected metre units')
        # In Isaac 6, NewtonArticulationRootAPI includes the USD root API as
        # a built-in schema. Count directly applied roots for ownership, and
        # report the composed roots too instead of hiding that distinction.
        roots = [str(prim.GetPath()) for prim in stage.Traverse()
                 if 'PhysicsArticulationRootAPI' in
                 prim.GetPrimTypeInfo().GetAppliedAPISchemas()]
        composed_roots = [str(prim.GetPath()) for prim in stage.Traverse()
                          if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
        if roots != [info['articulation_root']]:
            raise ValueError(f'{model}: unexpected articulation roots: {roots}')
        joint = stage.GetPrimAtPath(info['driven_joint_path'])
        if not joint or not joint.IsA(UsdPhysics.Joint):
            raise ValueError(f'{model}: driven joint is missing')
        report['models'][model] = {'default_prim': info['default_prim'],
                                   'articulation_root': roots[0],
                                   'composed_articulation_roots': composed_roots,
                                   'layers': len(layers)}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--manifest-only', action='store_true',
                        help='Check file integrity without importing USD or Isaac Sim')
    args = parser.parse_args()
    app = None
    try:
        if not args.manifest_only:
            from isaacsim import SimulationApp
            app = SimulationApp({'headless': True})
        print(json.dumps(validate(args.root, manifest_only=args.manifest_only), indent=2))
    finally:
        if app is not None:
            app.close()


if __name__ == '__main__':
    main()
