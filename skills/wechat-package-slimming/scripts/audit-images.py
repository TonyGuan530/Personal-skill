"""Read-only shipping-image inventory; no automatic unused-asset decisions."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.project.resolve()
    config = json.loads((root / 'project.config.json').read_text(encoding='utf-8-sig'))
    source = (root / config.get('miniprogramRoot', 'minigame')).resolve()
    if not source.is_relative_to(root) or not source.is_dir():
        raise ValueError('Invalid shipping root')
    output = args.output.resolve()
    if output.is_relative_to(source) or output == (root / 'project.config.json').resolve():
        raise ValueError('Audit output must not overwrite shipping files or project config')
    rows, hashes = [], {}
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'}:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError('Image escaped shipping root')
        with Image.open(path) as image:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            name = path.relative_to(root).as_posix()
            hashes.setdefault(digest, []).append(name)
            rows.append({'path': name, 'bytes': path.stat().st_size, 'width': image.width,
                         'height': image.height, 'mode': image.mode,
                         'hasAlpha': 'A' in image.getbands() or 'transparency' in image.info,
                         'decodedRGBAEstimateBytes': image.width * image.height * 4,
                         'sha256': digest})
    report = {'measurement': 'raw image source bytes, not platform upload size or measured memory',
              'images': sorted(rows, key=lambda row: row['bytes'], reverse=True),
              'byteIdenticalGroups': [names for names in hashes.values() if len(names) > 1]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'images': len(rows), 'bytes': sum(row['bytes'] for row in rows)}))


if __name__ == '__main__':
    main()
