"""Resize explicitly planned PNGs with DPR and rendered-image quality gates.

Requires Pillow. Dry-run by default. Crops are in ORIGINAL source coordinates;
the game's atlas/anchor code must independently support the new resolution.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
from PIL import Image, ImageChops

spec = importlib.util.spec_from_file_location('png_encoding', Path(__file__).with_name('optimize-package-images.py'))
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)


def alpha_stats(before, after):
    counts = ImageChops.difference(before.getchannel('A'), after.getchannel('A')).histogram()
    total = sum(counts)
    running, p99 = 0, 0
    for value, count in enumerate(counts):
        running += count
        if running >= total * .99:
            p99 = value
            break
    return {'rmse': math.sqrt(sum(i * i * n for i, n in enumerate(counts)) / total),
            'p99': p99, 'maximum': max(i for i, n in enumerate(counts) if n)}


def render_quality(before, after):
    metrics = png.quality(before, after)
    metrics['alpha'] = alpha_stats(before, after)
    return metrics


def acceptable(metrics):
    return bool(metrics.get('regions')) and all(
        region['dimensionsMatch']
        and region['alpha']['rmse'] <= 1.5 and region['alpha']['p99'] <= 4
        and region['alpha']['maximum'] <= 32
        and all(bg['rmse'] <= 2 and bg['p99'] <= 6 and bg['maximum'] <= 48
                for bg in region['backgrounds']) for region in metrics['regions'])


def resized(image, size, box=None):
    # Premultiply alpha before filtering to avoid colored transparent fringes.
    return image.convert('RGBa').resize(size, Image.Resampling.LANCZOS, box=box).convert('RGBA')


def evaluate_resize(path, plan):
    with Image.open(path) as source:
        if source.format != 'PNG' or getattr(source, 'is_animated', False) or Path(path).read_bytes()[24] > 8:
            raise ValueError('Only static 8-bit PNG resizing is supported')
        w, h = plan['width'], plan['height']
        if not all(isinstance(value, int) and value > 0 for value in [w, h]):
            raise ValueError('Invalid target dimensions')
        if w > source.width or h > source.height:
            raise ValueError('Upscaling is not package slimming')
        if abs(w / source.width - h / source.height) > 1e-6:
            raise ValueError('Target aspect must match source')
        if not plan.get('regions') or not isinstance(plan.get('dpr'), (int, float)) or plan['dpr'] <= 0:
            raise ValueError('Explicit display regions and DPR required')
        original = source.convert('RGBA')
        candidate = resized(original, (w, h))
        regions = []
        for item in plan['regions']:
            x, y, rw, rh = item['rect']
            if x < 0 or y < 0 or rw <= 0 or rh <= 0 or x + rw > source.width or y + rh > source.height:
                raise ValueError('Invalid source frame')
            display = item['logicalSize'] * plan['dpr']
            if not math.isfinite(display) or display <= 0:
                raise ValueError('Invalid display size')
            factor = display / max(rw, rh)
            size = (max(1, round(rw * factor)), max(1, round(rh * factor)))
            xs, ys = w / source.width, h / source.height
            if rw * xs < size[0] or rh * ys < size[1]:
                raise ValueError('Insufficient DPR coverage for source frame')
            before = resized(original, size, (x, y, x + rw, y + rh))
            after = resized(candidate, size, (x * xs, y * ys, (x + rw) * xs, (y + rh) * ys))
            metrics = render_quality(before, after)
            metrics.update({'name': item.get('name', ''), 'physicalDisplaySize': size,
                            'candidateFrameSize': [rw * xs, rh * ys]})
            regions.append(metrics)
        return png.encode(candidate, source), {'regions': regions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = args.project.resolve()
    project = json.loads((root / 'project.config.json').read_text(encoding='utf-8-sig'))
    shipping = (root / project.get('miniprogramRoot', 'minigame')).resolve()
    if not shipping.is_relative_to(root) or not shipping.is_dir():
        raise ValueError('Invalid shipping root')
    backup = args.backup.resolve()
    if backup.is_relative_to(shipping):
        raise ValueError('Backups must be outside the shipping package')
    report_path = args.report.resolve()
    if (report_path.is_relative_to(shipping) or report_path.is_relative_to(backup)
            or report_path in {args.plan.resolve(), (root / 'project.config.json').resolve()}):
        raise ValueError('Report must not overwrite shipping files, backups, plan or project config')
    plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
    rows, staged, seen = [], [], set()
    for item in plan['images']:
        relative = Path(item['path'])
        path = root / relative
        if relative.is_absolute() or '..' in relative.parts or path.is_symlink() or not path.resolve().is_relative_to(shipping):
            raise ValueError('Image escaped shipping root')
        if path.resolve() in seen:
            raise ValueError('Duplicate planned image')
        seen.add(path.resolve())
        before = path.read_bytes()
        data, metrics = evaluate_resize(path, item)
        selected = acceptable(metrics) and len(data) < len(before)
        target = backup / relative
        if target.is_symlink() or not target.resolve().is_relative_to(backup):
            raise ValueError('Backup target escaped backup root')
        if args.apply and selected and target.exists() and target.read_bytes() != before:
            raise ValueError(f'Backup conflict: {target}')
        rows.append({'path': item['path'], 'beforeBytes': len(before), 'candidateBytes': len(data),
                     'accepted': selected, 'applied': args.apply and selected,
                     'targetSize': [item['width'], item['height']], 'quality': metrics,
                     'beforeSha256': hashlib.sha256(before).hexdigest(),
                     'candidateSha256': hashlib.sha256(data).hexdigest()})
        if selected:
            staged.append((path, target, before, data))
    # Evaluate every image/backup before mutating any source.
    batch_accepted = bool(rows) and all(row['accepted'] for row in rows)
    if args.apply and batch_accepted:
        for path, target, before, data in staged:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(before)
            path.write_bytes(data)
    if not batch_accepted:
        for row in rows:
            row['applied'] = False
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {'applied': args.apply and batch_accepted, 'savedBytes': sum(row['beforeBytes'] - row['candidateBytes']
              for row in rows if row['accepted']), 'images': rows}
    args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'applied': report['applied'], 'accepted': sum(row['accepted'] for row in rows),
                      'images': len(rows), 'savedBytes': report['savedBytes']}))
    if not batch_accepted:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
