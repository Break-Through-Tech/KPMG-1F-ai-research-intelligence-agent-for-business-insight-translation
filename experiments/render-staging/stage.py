"""Copy only runtime inputs into a fresh, private Docker build context."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

from engine_runtime import RUNTIME_FILES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UI_FILES = 'index.html app.js async-guards.js chart-select.js chart-svg.js consult.css evidence.js prefs.js kpmg-logo-white.png'
SHARED = 'answer-export.js math.js read-aloud.css read-aloud.mjs research-speech.js source-reader.js'
BUNDLE = ('manifest.json', 'parents.jsonl', 'views.json', 'vectors.npy')
MODEL_SUFFIXES = {'.json', '.safetensors', '.txt', '.model'}
EXPECTED_INDEX = '78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa'


def checksum(path):
    with path.open('rb') as stream:
        from hashlib import file_digest
        return file_digest(stream, 'sha256').hexdigest()


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = checksum(source)
    shutil.copyfile(source, target)
    if checksum(target) != digest or checksum(source) != digest:
        raise ValueError('A source changed during snapshotting. Build a new snapshot.')
    return digest


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError('The UI refresh changed a staging hook. Inspect before rebuilding.')
    return text.replace(old, new, 1)


def snapshot(args):
    output = args.output.resolve()
    if not output.is_relative_to(HERE) or output == HERE:
        raise ValueError('Choose a new Render experiment output directory.')
    synthetic = getattr(args, 'synthetic_fixture', False)
    pin = EXPECTED_INDEX
    if synthetic:
        expected = json.loads((ROOT / 'onboarding/fixture-assets.json').read_bytes())
        for name in BUNDLE:
            if checksum(args.bundle / name) != expected['demo-100/' + name]['sha256']:
                raise ValueError('Synthetic fixture bundle checksum mismatch.')
        if checksum(args.audit) != expected['table-audit-demo-100.json']['sha256']:
            raise ValueError('Synthetic fixture audit checksum mismatch.')
        pin = expected['demo-100/parents.jsonl']['sha256']
    if checksum(args.bundle / 'parents.jsonl') != pin:
        raise ValueError('The supplied index is not the pinned demo-100 bundle.')
    output.mkdir()
    hashes = {}
    sources = {}

    def add(source, dest):
        sources[dest] = copy(source, output / dest)
        hashes[dest] = sources[dest]

    candidate = args.ui / 'ui-consult/design/merge-with-codex'
    expected = {'app.js': '05f8afa904f6848c', 'consult.css': '7d4d9060f450f9bf',
                'index.html': 'd4dd018fe1e14329', 'mock-api.js': 'dd6d469be53c6b59',
                'serve.py': '102f32391cc5dcf9'}
    for name, prefix in expected.items():
        if not checksum(candidate / name).startswith(prefix):
            raise ValueError(f'Handoff checksum mismatch: {name}')

    for srcdir, filenames in ((args.ui / 'ui-consult', UI_FILES), (args.ui / 'ui', SHARED)):
        for name in filenames.split():
            source = candidate / name if name in ('app.js', 'consult.css', 'index.html') else srcdir / name
            add(source, f'snapshot/assets/{name}')
    ui = output / 'snapshot/assets'
    html = (ui / 'index.html').read_text(encoding='utf-8')
    (ui / 'index.html').write_text(replace(html, '  <script src="/mock-api.js" defer></script>\n', ''), encoding='utf-8')
    app = (ui / 'app.js').read_text(encoding='utf-8')
    for old, new in (
        ('interpret_context: true,', 'interpret_context: false,'),
        ("$('#industry-field').hidden = !indexedMode;", "$('#industry-field').hidden = true;"),
        ("$('#risk-field').hidden = !indexedMode || mock;", "$('#risk-field').hidden = true;"),
    ):
        app = replace(app, old, new)
    (ui / 'app.js').write_text(app, encoding='utf-8')
    export = ui / 'answer-export.js'
    text = export.read_text(encoding='utf-8')
    text = replace(text, "    const result = demo.result;", """    const result = demo.result;
    const version = demo.library?.version;
    const latest = demo.library?.reviews?.at(-1);
    const decision = version && latest?.version_id === version.id && latest.fingerprint === version.fingerprint
      ? {approve: 'Approved', revise: 'Changes requested', reject: 'Rejected'}[latest.decision] : null;""")
    text = replace(text, "    add('p', 'Human review: pending. Approved: false. This export is not approval, source certification, or verification of semantic support.');",
                   """    add('p', 'Exported content: original research draft.');
    add('p', decision ? 'Recorded review for this version: ' + decision + '. Reviewer identity is self-reported.' :
      'No matching review decision was recorded for this export.');""")
    text = replace(text, 'Pending review; not approved. Check your browser downloads.',
                   'Original draft and available version review status. Check your browser downloads.')
    export.write_text(text, encoding='utf-8')
    for name in ('app.js', 'index.html', 'answer-export.js'):
        hashes[f'snapshot/assets/{name}'] = checksum(ui / name)

    vendor = args.ui / 'ui/vendor/katex'
    for path in (vendor / 'katex.min.js', vendor / 'katex.min.css', vendor / 'LICENSE',
                 *sorted((vendor / 'fonts').glob('*.woff2'))):
        add(path, 'snapshot/assets/vendor/katex/' + path.relative_to(vendor).as_posix())
    # Bundled interface fonts (SIL OFL 1.1) and their licence texts, served at /fonts/.
    fonts = args.ui / 'ui-consult/fonts'
    for path in sorted(fonts.glob('*.woff2')) + sorted(fonts.glob('LICENSE-*.txt')):
        add(path, 'snapshot/assets/fonts/' + path.name)
    for name in BUNDLE:
        add(args.bundle / name, f'snapshot/artifacts/bundle/{name}')
    add(args.audit, 'snapshot/artifacts/table-audit.json')
    for name in ('encoder', 'reranker'):
        model = getattr(args, name)
        for path in sorted(model.rglob('*')):
            if path.is_file() and path.suffix in MODEL_SUFFIXES:
                add(path, f'snapshot/artifacts/{name}/' + path.relative_to(model).as_posix())
        if not (output / f'snapshot/artifacts/{name}/model.safetensors').is_file():
            raise ValueError('The exact local safetensors model is required.')
    for path in sorted((ROOT / 'src').rglob('*.py')):
        add(path, path.relative_to(ROOT).as_posix())
    for name in ('recorded_backend.py', 'evidence_tables.py', 'chart_preview.py'):
        add(ROOT / f'experiments/table-endpoint/{name}', f'experiments/table-endpoint/{name}')
    prompt = 'prompts/business_translation/baseline-v1.txt'
    add(ROOT / prompt, prompt)
    downstream = 'prompts/business_translation/downstream-v1.2.txt'
    add(ROOT / downstream, 'snapshot/' + downstream)
    add(ROOT / downstream, downstream)
    for name in ('server.py', 'engine_runtime.py', 'dev_server.py', 'smoke_server.py'):
        add(HERE / name, f'experiments/render-staging/{name}')
    for folder, modules in RUNTIME_FILES.items():
        for module in modules.split():
            name = f'experiments/{folder}/{module}.py'
            add(ROOT / name, name)
    for name in ('Dockerfile', 'requirements.txt'):
        add(HERE / name, name)

    def head(path):
        return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()

    manifest = {'backend_head': head(ROOT), 'frontend_head': head(args.ui),
                'source_sha256': sources,
                'files': {name.removeprefix('snapshot/'): digest for name, digest in hashes.items()
                          if name.startswith('snapshot/')}}
    if synthetic:
        manifest['synthetic_fixture'] = True
    (output / 'snapshot/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Staged {len(hashes)} allowlisted files at {sum(p.stat().st_size for p in output.rglob("*") if p.is_file())} bytes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for option in ('output', 'ui', 'bundle', 'audit', 'encoder', 'reranker'):
        parser.add_argument(f'--{option}', required=True, type=Path)
    parser.add_argument('--synthetic-fixture', action='store_true')
    snapshot(parser.parse_args())
