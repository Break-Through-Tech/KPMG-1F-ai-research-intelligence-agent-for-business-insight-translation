"""Verify and prepare local release attachments after project approval. Never uploads."""
import argparse
import json
from pathlib import Path
import shutil
import sys

from setup import ROOT, SetupError, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True, help='Directory with assets.json relative file layout')
    parser.add_argument('--output', type=Path, required=True, help='A new private directory outside the checkout')
    parser.add_argument('--clearance-reference', required=True, help='Recorded approval reference for exact data and audience')
    args = parser.parse_args()
    if not args.clearance_reference.strip():
        raise SetupError('A recorded project approval reference is required.')
    if args.output.resolve().is_relative_to(ROOT):
        raise SetupError('Use a private output directory outside the Git checkout.')
    spec = json.loads((ROOT / 'onboarding/assets.json').read_bytes())
    files = {name: item for name, item in spec['files'].items() if item['source'] == 'release'}
    for name, item in files.items():
        verify(args.assets / name, item)
    args.output.mkdir()
    for name, item in files.items():
        path = args.output / item['release_asset']
        shutil.copyfile(args.assets / name, path)
        verify(path, item)
    print(f'Prepared {len(files)} verified local attachments for {spec["release_tag"]}.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, SetupError) as error:
        sys.exit(f'Attachment preparation failed: {error}')
