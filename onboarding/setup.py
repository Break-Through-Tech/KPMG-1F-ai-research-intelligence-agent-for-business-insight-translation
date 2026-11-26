"""Portable setup for the supervised offline research application."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/render-staging'
CACHE = ROOT / '.kpmg-onboarding'
FRONTEND = ROOT / 'onboarding/frontend'
IMAGE = 'kpmg-research-offline:local'
MODEL_PINS = {
    'encoder': 'sentence-transformers/all-MiniLM-L6-v2/resolve/1110a243fdf4706b3f48f1d95db1a4f5529b4d41',
    'reranker': 'cross-encoder/ms-marco-MiniLM-L6-v2/resolve/233902d25c440f23af6f7d6e94d2946bac0bee0a',
}


class SetupError(Exception):
    pass


def run(command, *, capture=False):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=capture)
    if result.returncode:
        raise SetupError(f'{Path(command[0]).name} command failed. {result.stderr.strip() if capture else "See output above."}')
    return result.stdout.strip() if capture else None


def exists(command):
    path = shutil.which(command)
    if not path:
        raise SetupError(f'{command} is required. See onboarding/README.md.')
    return path


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(path, expected):
    if not path.is_file() or path.is_symlink():
        raise SetupError(f'Missing verified file: {path.name}')
    if path.stat().st_size != expected['bytes'] or sha256(path) != expected['sha256']:
        raise SetupError(f'Checksum or size mismatch: {path.name}. Replace the damaged cache from the approved release.')


def acquire(spec, cache, repository=None):
    cache.mkdir(parents=True, exist_ok=True)
    missing = []
    for name, item in spec['files'].items():
        path = cache / name
        if path.exists():
            verify(path, item)
        else:
            missing.append((name, item))
    if not missing:
        return
    if not repository:
        raise SetupError('No private asset repository configured. Supply --asset-repo OWNER/REPO '
                         'after the project owner provisions and clears the private release.')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise SetupError('Specify a private GitHub asset repository as OWNER/REPO.')
    gh = exists('gh')
    try:
        visibility = run([gh, 'repo', 'view', repository, '--json', 'visibility',
                          '--jq', '.visibility'], capture=True)
    except SetupError as error:
        raise SetupError('Authenticate GitHub CLI with gh auth login and request project repository access.') from error
    if visibility != 'PRIVATE':
        raise SetupError('The configured asset release repository must be private.')
    with tempfile.TemporaryDirectory(prefix='download-', dir=cache) as tmp:
        args = [gh, 'release', 'download', spec['release_tag'], '--repo', repository, '--dir', tmp]
        for _, item in missing:
            args.extend(('--pattern', item['release_asset']))
        try:
            run(args, capture=True)
        except SetupError as error:
            raise SetupError(f'Private asset release {spec["release_tag"]} is unavailable. '
                             'Check repository access. Publication of the exact corpus is pending project data-use clearance.') from error
        for _, item in missing:
            verify(Path(tmp) / item['release_asset'], item)
        for name, item in missing:
            path = cache / name
            path.parent.mkdir(parents=True, exist_ok=True)
            (Path(tmp) / item['release_asset']).replace(path)


def origin_repository():
    try:
        origin = run([exists('git'), 'remote', 'get-url', 'origin'], capture=True)
    except SetupError:
        return None
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', origin)
    return match[1].removesuffix('.git') if match else None


def acquire_fixture(spec, cache):
    fixture = ROOT / 'onboarding/fixture'
    for name, item in spec['files'].items():
        target = cache / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
                staged = Path(tmp) / target.name
                if name.startswith('models/'):
                    _, kind, key = name.split('/', 2)
                    url = f'https://huggingface.co/{MODEL_PINS[kind]}/{key}'
                    print(f'Fetching pinned public model file: {name}', flush=True)
                    with urlopen(url, timeout=60) as source, staged.open('wb') as dest:
                        remaining = item['bytes']
                        while remaining:
                            block = source.read(min(1024 * 1024, remaining))
                            if not block:
                                break
                            dest.write(block)
                            remaining -= len(block)
                        if remaining or source.read(1):
                            raise SetupError(f'Unexpected download length: {name}')
                else:
                    shutil.copyfile(fixture / name, staged)
                verify(staged, item)
                staged.replace(target)
        verify(target, item)


def prepare(spec, cache, *, synthetic=False):
    present = {p.relative_to(cache).as_posix() for model in ('encoder', 'reranker')
               for p in (cache / 'models' / model).rglob('*') if p.is_file()}
    expected_models = {name for name in spec['files'] if name.startswith('models/')}
    if present != expected_models:
        raise SetupError('Unexpected model cache content. Use only the exact files in assets.json.')
    observed_ui = {p.relative_to(FRONTEND).as_posix()
                   for p in FRONTEND.rglob('*') if p.is_file()}
    if observed_ui != set(spec['frontend']):
        raise SetupError('Frontend directory differs from the approved allowlist.')
    for name, expected in spec['frontend'].items():
        path = FRONTEND / name
        if not path.is_file() or sha256(path) != expected:
            raise SetupError(f'Approved frontend checksum mismatch: {name}. Restore the file from Git.')
    git = exists('git')
    # Fresh context each time keeps stale source or assets out of the runtime.
    with tempfile.TemporaryDirectory(prefix='image-context-prepare-', dir=HERE) as temp:
        output = Path(temp) / 'context'
        run([sys.executable, '-B', str(HERE / 'stage.py'), '--output', str(output),
             '--ui', str(FRONTEND), '--bundle', str(cache / 'demo-100'),
             '--audit', str(cache / 'table-audit-demo-100.json'),
             '--encoder', str(cache / 'models/encoder'), '--reranker', str(cache / 'models/reranker'),
             *(['--synthetic-fixture'] if synthetic else [])])
        for name, destination in [('requirements-py311.lock.txt', 'requirements.txt'), ('Dockerfile', 'Dockerfile')]:
            shutil.copyfile(ROOT / 'onboarding' / name, output / destination)
        verify_snapshot = json.loads((output / 'snapshot/manifest.json').read_bytes())
        for name, expected in verify_snapshot['files'].items():
            path = output / 'snapshot' / name
            if sha256(path) != expected:
                raise SetupError(f'Staged asset checksum mismatch: {name}')
        parent = HERE / 'image-context-onboarding'
        parent.mkdir(exist_ok=True)
        revision = run([git, 'rev-parse', '--short', 'HEAD'], capture=True)
        with tempfile.TemporaryDirectory(prefix=f'{revision}-', dir=parent) as holder:
            target = Path(holder).with_name(Path(holder).name + '-ready')
            shutil.move(str(output), str(target))
    (cache.parent / 'context.txt').write_text(str(target.relative_to(ROOT)) + '\n', encoding='utf-8')
    return target


def native_python(cache=CACHE):
    return cache / ('venv/Scripts/python.exe' if os.name == 'nt' else 'venv/bin/python')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('setup', 'start'), nargs='?', default='setup')
    parser.add_argument('--runtime', choices=('docker', 'native'), default='docker')
    parser.add_argument('--prepare-only', action='store_true', help='Verify and stage without building or installing.')
    parser.add_argument('--asset-repo', default=os.environ.get('KPMG_ASSET_REPO'),
                        help='Approved private GitHub repository in OWNER/REPO form')
    parser.add_argument('--fixture', action='store_true', help='Use public models and synthetic test data only')
    parser.add_argument('--engine', choices=('baseline', 's2'), default='baseline')
    args = parser.parse_args()
    if sys.version_info[:2] < (3, 11):
        raise SetupError('Python 3.11 or newer is required for setup.')
    if args.runtime == 'native' and sys.version_info[:2] != (3, 11):
        raise SetupError('Run native setup using Python 3.11.')
    if args.action == 'start' or not args.prepare_only:
        if args.runtime == 'docker':
            docker = exists('docker')
            try:
                os_type = run([docker, 'info', '--format', '{{.OSType}}'], capture=True)
            except SetupError as error:
                raise SetupError('Docker Engine is unavailable. Start Docker Desktop/Engine, or choose native Python 3.11.') from error
            if os_type != 'linux':
                raise SetupError('Switch Docker to Linux containers.')
    spec = json.loads((ROOT / 'onboarding/assets.json').read_bytes())
    workspace = CACHE / 'fixture' if args.fixture else CACHE
    image = 'kpmg-research-synthetic:local' if args.fixture else IMAGE
    volume = 'kpmg-synthetic-state' if args.fixture else 'kpmg-offline-state'
    if args.action == 'setup':
        if args.fixture:
            synthetic = json.loads((ROOT / 'onboarding/fixture-assets.json').read_bytes())
            spec['files'] = {**synthetic, **{p: item for p, item in spec['files'].items()
                                             if p.startswith('models/')}}
            acquire_fixture(spec, workspace / 'assets')
        else:
            acquire(spec, workspace / 'assets', args.asset_repo or origin_repository())
        context = prepare(spec, workspace / 'assets', synthetic=args.fixture)
        if not args.prepare_only:
            if args.runtime == 'docker':
                run([docker, 'build', '--platform', 'linux/amd64', '-t', image, str(context)])
            else:
                python = native_python(workspace)
                if not python.is_file():
                    run([sys.executable, '-m', 'venv', str(workspace / 'venv')])
                run([str(python), '-m', 'pip', 'install', '--index-url',
                     'https://download.pytorch.org/whl/cpu', '--no-deps', 'torch==2.15.0+cpu'])
                run([str(python), '-m', 'pip', 'install', '--no-deps', '-r', str(context / 'requirements.txt')])
                run([str(python), '-m', 'pip', 'check'])
        print('Verified runtime context:', context.relative_to(ROOT))
        return
    if args.prepare_only:
        raise SetupError('--prepare-only is only supported during setup.')
    command = ['experiments/render-staging/dev_server.py', '--engine', args.engine,
               *(['--fixture'] if args.fixture else [])]
    if args.runtime == 'docker':
        run([docker, 'run', '--rm', '--platform', 'linux/amd64', '-p', '127.0.0.1:8821:8821',
             '--mount', f'type=volume,source={volume},target=/state', image,
             'python', '-B', *command, '--snapshot', '/app/snapshot', '--state', '/state', '--container'])
    else:
        python = native_python(workspace)
        if not python.is_file() or not (workspace / 'context.txt').is_file():
            raise SetupError('Run native setup first.')
        context = ROOT / (workspace / 'context.txt').read_text(encoding='utf-8').strip()
        run([str(python), '-B', str(context / command[0]), '--engine', args.engine,
             '--snapshot', str(context / 'snapshot'), '--state', str(workspace / 'state')])


if __name__ == '__main__':
    try:
        main()
    except (SetupError, OSError) as error:
        sys.exit(f'Setup error: {error}')
