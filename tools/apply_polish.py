"""Run polish steps on a package: enforce strong hook and run thresholds dry-run."""
import subprocess
import sys
from pathlib import Path


def run_cmd(args):
    print('>',' '.join(args))
    res = subprocess.run(args, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    return res.returncode


def main(pkg_path: str):
    pkg = Path(pkg_path)
    if not pkg.exists():
        print('Package not found:', pkg)
        return 2

    # 1) enforce strong hook and replace if weak
    print('1) Enforcing strong hook (strict + replace)')
    rc = run_cmd([sys.executable, 'tools/enforce_hook.py', str(pkg / 'script.txt'), '--strict', '--replace'])
    if rc != 0:
        print('Hook enforcement returned', rc)

    # 1b) generate A/B hook variants and save to title_options.txt
    try:
        print('\n1b) Generating A/B hook variants')
        res = subprocess.run([sys.executable, 'tools/enforce_hook.py', '--variants', str(pkg / 'script.txt')], capture_output=True, text=True)
        print(res.stdout)
        # expect JSON-like text in stdout; to be robust, call generate via module instead
        # fallback: call a small python snippet to import and write
        from pathlib import Path as _P
        p = _P(pkg) / 'title_options.txt'
        # run a direct import to get variants
        import importlib, sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        eh = importlib.import_module('tools.enforce_hook')
        variants = eh.generate_hook_variants((p.parent / 'script.txt').read_text(encoding='utf-8'))
        with open(p, 'w', encoding='utf-8') as f:
            for v in variants:
                f.write(v['hook'] + '\n')
        print('Wrote hook variants to', p)
    except Exception as e:
        print('Hook variant generation failed:', e)

    # 2) thresholds dry-run: default and lenient
    print('\n2) Running thresholds dry-run (default)')
    run_cmd([sys.executable, 'tools/thresholds_dry_run.py', str(pkg)])

    print('\n3) Running thresholds dry-run (lenient)')
    run_cmd([sys.executable, 'tools/thresholds_dry_run.py', str(pkg), '--min-motion', '0.01', '--motion-thresholds', '{"thumbnail": 0.005, "clip": 0.01}'])

    print('\nPolish complete. See visuals_pruned_preview.json files in package folder for previews.')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/apply_polish.py <package_path>')
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
