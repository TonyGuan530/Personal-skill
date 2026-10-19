"""Conservative PNG optimization. Dry run by default; requires Pillow.

No resizing. Alpha must match exactly. RGB rounding changes each visible
channel by at most two levels; transparent RGB is normalized to zero.
Originals are backed up outside the shipping package before --apply.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from PIL import Image, ImageChops


def quality(source, candidate):
    source, candidate = source.convert('RGBA'), candidate.convert('RGBA')
    if source.size != candidate.size:
        return {'dimensionsMatch': False, 'alphaExact': False}
    metrics = {'dimensionsMatch': True,
               'alphaExact': source.getchannel('A').tobytes() == candidate.getchannel('A').tobytes(),
               'backgrounds': []}
    for color in [(23, 31, 35), (241, 226, 196), (255, 255, 255)]:
        background = Image.new('RGBA', source.size, (*color, 255))
        before = Image.alpha_composite(background, source).convert('RGB')
        after = Image.alpha_composite(background, candidate).convert('RGB')
        histogram = ImageChops.difference(before, after).histogram()
        counts = [sum(histogram[i + channel * 256] for channel in range(3)) for i in range(256)]
        total = sum(counts)
        cumulative = 0
        percentile = 0
        for value, count in enumerate(counts):
            cumulative += count
            if cumulative >= total * .99:
                percentile = value
                break
        metrics['backgrounds'].append({'rgb': color,
            'rmse': math.sqrt(sum(i * i * n for i, n in enumerate(counts)) / total),
            'p99': percentile, 'maximum': max(i for i, n in enumerate(counts) if n)})
    return metrics


def acceptable(metrics):
    return (metrics.get('dimensionsMatch') and metrics.get('alphaExact')
            and all(item['rmse'] <= 1.5 and item['p99'] <= 2 and item['maximum'] <= 2
                    for item in metrics['backgrounds']))


def encode(image, source):
    output = io.BytesIO()
    options = {'optimize': True, 'compress_level': 9}
    if source.info.get('icc_profile'):
        options['icc_profile'] = source.info['icc_profile']
    if source.info.get('gamma') is not None:
        # Preserve PNG color interpretation metadata.
        from PIL.PngImagePlugin import PngInfo
        import struct
        metadata = PngInfo()
        metadata.add(b'gAMA', struct.pack('>I', round(source.info['gamma'] * 100000)))
        options['pnginfo'] = metadata
    if source.info.get('srgb') is not None:
        from PIL.PngImagePlugin import PngInfo
        metadata = options.setdefault('pnginfo', PngInfo())
        metadata.add(b'sRGB', bytes([source.info['srgb']]))
    if source.info.get('chromaticity') is not None:
        from PIL.PngImagePlugin import PngInfo
        import struct
        metadata = options.setdefault('pnginfo', PngInfo())
        metadata.add(b'cHRM', struct.pack('>8I', *(round(value * 100000) for value in source.info['chromaticity'])))
    if source.info.get('exif'):
        options['exif'] = source.info['exif']
    image.save(output, format='PNG', **options)
    return output.getvalue()


def optimize_image(path):
    original = Path(path).read_bytes()
    with Image.open(io.BytesIO(original)) as source:
        if getattr(source, 'is_animated', False) or original[24] > 8:
            return original, 'original-high-depth-or-animated', quality(source, source)
        rgba = source.convert('RGBA')
        best, method, metrics = original, 'original', quality(rgba, rgba)
        invisible = rgba.getchannel('A').point(lambda alpha: 255 if alpha == 0 else 0)
        normalized = rgba.copy()
        normalized.paste((0, 0, 0, 0), (0, 0), invisible)
        rounded = normalized.copy()
        channels = rounded.split()
        rounded = Image.merge('RGBA', tuple(channel.point(lambda value: min(255, ((value + 2) // 4) * 4))
                                            for channel in channels[:3]) + (channels[3],))
        for label, candidate in [('lossless-visible', normalized), ('rgb-step4-alpha-exact', rounded)]:
            data = encode(candidate, source)
            candidate_metrics = quality(rgba, candidate)
            if len(data) < len(best) and acceptable(candidate_metrics):
                best, method, metrics = data, label, candidate_metrics
        return best, method, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    root = args.project.resolve()
    config_path = root / 'project.config.json'
    project = json.loads(config_path.read_text(encoding='utf-8-sig')) if config_path.exists() else {}
    shipping = (root / project.get('miniprogramRoot', 'minigame')).resolve()
    if not shipping.is_relative_to(root) or not shipping.is_dir():
        raise ValueError('Invalid or missing shipping root')
    backup = root / 'tmp/package-optimization/originals'
    if backup.resolve().is_relative_to(shipping):
        raise ValueError('Backup must be outside shipping root')
    if args.report:
        report_path = args.report.resolve()
        if report_path.is_relative_to(shipping) or report_path.is_relative_to(backup.resolve()) or report_path == config_path.resolve():
            raise ValueError('Report must not overwrite shipping files, backups or project config')
    rows = []
    for path in sorted(shipping.rglob('*.png')):
        if path.is_symlink() or not path.resolve().is_relative_to(shipping):
            raise RuntimeError(f'Image outside shipping directory: {path}')
        before = path.read_bytes()
        if len(before) < 32768:
            continue
        data, method, metrics = optimize_image(path)
        relative = path.relative_to(root)
        selected = len(data) <= len(before) * .97 and len(before) - len(data) >= 1024
        if not selected:
            data, method = before, 'original-small-saving'
        if args.apply and selected:
            target = backup / relative
            if target.is_symlink() or not target.resolve().is_relative_to(backup.resolve()):
                raise ValueError('Backup target escaped backup root')
            if target.exists() and target.read_bytes() != before:
                raise RuntimeError(f'Backup conflict; refusing overwrite: {target}')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(before)
            path.write_bytes(data)
        rows.append({'path': relative.as_posix(), 'before': len(before), 'after': len(data),
                     'method': method, 'metrics': metrics, 'applied': args.apply and selected,
                     'beforeSha256': hashlib.sha256(before).hexdigest(),
                     'afterSha256': hashlib.sha256(data).hexdigest()})
    report = {'applied': args.apply, 'savedBytes': sum(row['before'] - row['after'] for row in rows),
              'images': rows}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'applied': args.apply, 'images': len(rows), 'savedBytes': report['savedBytes']}))


if __name__ == '__main__':
    main()
