# -*- coding: utf-8 -*-
"""
Normaliza las imágenes antiguas de resources/images (subidas antes de que
handler_images.py limitara el tamaño): aplica la orientación EXIF, limita el lado
mayor a IMAGE_MAX_SIDE y re-codifica. Así el amblemario y los PDFs no descargan
fotos de 4000+ px.

- Conserva nombre y extensión de cada archivo: no hay que tocar Mongo.
  JPEG sigue siendo JPEG y PNG sigue siendo PNG.
- Solo procesa archivos con lado mayor > --max-side o con orientación EXIF.
  GIF, SVG y demás formatos se ignoran.
- Una imagen redimensionada se reemplaza si no queda más pesada; una que solo
  necesita corregir la orientación, si ahorra al menos --min-saving %.
- Escritura atómica (archivo temporal + rename) conservando permisos y dueño.
- Compatible con Python 2.7 + Pillow 6 (producción) y 3.6 + Pillow 8 (Docker local).

Uso:
  python scripts/normalize_legacy_images.py                                # simulación, no escribe
  python scripts/normalize_legacy_images.py --only peca_project --limit 50
  python scripts/normalize_legacy_images.py --apply --backup-dir /ruta/respaldo
  python scripts/normalize_legacy_images.py --restore /ruta/respaldo

Con --apply cada original se copia a --backup-dir (misma ruta relativa) antes de
reemplazarlo, y se registra en <backup-dir>/manifest.tsv. --restore lo revierte.
"""
from __future__ import division, print_function, unicode_literals

import argparse
import errno
import io
import os
import shutil
import sys
import tempfile
import time

from PIL import Image

PY2 = sys.version_info[0] < 3

ROOT_DEFAULT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'resources', 'images'))
MAX_SIDE_DEFAULT = int(os.getenv('IMAGE_MAX_SIDE', 1920))
QUALITY_DEFAULT = int(os.getenv('IMAGE_JPEG_QUALITY', 82))
EXTENSIONS = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.jpe': 'JPEG', '.png': 'PNG'}
MANIFEST = 'manifest.tsv'
TMP_PREFIX = '.normalize-'

EXIF_ORIENTATION = 0x0112
# EXIF orientation -> transpose operations (same table as ImageOps.exif_transpose)
ORIENTATION_OPS = {
    2: [Image.FLIP_LEFT_RIGHT],
    3: [Image.ROTATE_180],
    4: [Image.FLIP_TOP_BOTTOM],
    5: [Image.ROTATE_90, Image.FLIP_TOP_BOTTOM],
    6: [Image.ROTATE_270],
    7: [Image.ROTATE_270, Image.FLIP_TOP_BOTTOM],
    8: [Image.ROTATE_90],
}
LANCZOS = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', None))


def out(msg=''):
    # py2 + stdout redirected (log file) defaults to ascii; force utf-8
    if PY2:
        sys.stdout.write((msg + '\n').encode('utf-8'))
    else:
        print(msg)
    sys.stdout.flush()


def human(size):
    return '{:.1f} MB'.format(size / 1e6)


def get_orientation(image):
    try:
        exif = image._getexif() if hasattr(image, '_getexif') else None
    except Exception:
        return 1
    if not exif:
        return 1
    return exif.get(EXIF_ORIENTATION, 1) or 1


def needs_processing(image, max_side):
    return max(image.size) > max_side or get_orientation(image) in ORIENTATION_OPS


def normalize(path, fmt, max_side, quality):
    """Return (new_bytes, resized) or (None, reason) when the file must stay as is"""
    with open(path, 'rb') as f:
        image = Image.open(io.BytesIO(f.read()))
    real_fmt = str(image.format).upper()
    if fmt == 'JPEG' and real_fmt not in ('JPEG', 'MPO'):
        return None, 'formato real {} con extensión JPEG'.format(real_fmt)
    if fmt == 'PNG' and real_fmt != 'PNG':
        return None, 'formato real {} con extensión PNG'.format(real_fmt)
    if not needs_processing(image, max_side):
        return None, 'ya normalizada'

    orientation = get_orientation(image)
    if fmt == 'JPEG':
        # Decodes at 1/2, 1/4 or 1/8 directly: much faster and less memory for big photos
        image.draft('RGB', (max_side, max_side))
    image.load()

    for op in ORIENTATION_OPS.get(orientation, []):
        image = image.transpose(op)
    resized = max(image.size) > max_side
    if resized:
        if image.mode == 'P':
            image = image.convert('RGBA')  # palette images can only be resized with NEAREST
        image.thumbnail((max_side, max_side), LANCZOS)

    buffer = io.BytesIO()
    if fmt == 'JPEG':
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # EXIF is not kept: may carry GPS data and the orientation is already applied
        image.save(buffer, 'JPEG', quality=quality, optimize=True, progressive=True)
    else:
        if image.mode not in ('RGBA', 'LA', 'RGB', 'L', 'P'):
            image = image.convert('RGBA')
        image.save(buffer, 'PNG', optimize=True)
    return buffer.getvalue(), resized


def iter_files(root, only):
    base = os.path.join(root, only) if only else root
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for name in sorted(filenames):
            if name.startswith(TMP_PREFIX):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in EXTENSIONS:
                yield os.path.join(dirpath, name), EXTENSIONS[ext]


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def atomic_replace(path, content):
    """Write content over path keeping its permissions and owner"""
    st = os.stat(path)
    fd, tmp = tempfile.mkstemp(prefix=TMP_PREFIX, dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, st.st_mode & 0o7777)
        try:
            os.chown(tmp, st.st_uid, st.st_gid)
        except OSError:
            pass  # not root: the file keeps the current user, same as new uploads
        os.rename(tmp, path)  # atomic on POSIX, overwrites on py2 too
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def backup(path, root, backup_dir, manifest):
    rel = os.path.relpath(path, root)
    target = os.path.join(backup_dir, rel)
    if os.path.exists(target):
        raise RuntimeError('ya existe en el respaldo: {}'.format(target))
    makedirs(os.path.dirname(target))
    shutil.copy2(path, target)
    manifest.write((rel + '\n').encode('utf-8'))
    manifest.flush()


def run(args):
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        out('No existe el directorio: {}'.format(root))
        return 1

    manifest = None
    if args.apply:
        backup_dir = os.path.abspath(args.backup_dir)
        if backup_dir == root or backup_dir.startswith(root + os.sep):
            out('El respaldo no puede estar dentro de {}'.format(root))
            return 1
        makedirs(backup_dir)
        manifest = io.open(os.path.join(backup_dir, MANIFEST), 'ab')

    mode = 'APLICANDO' if args.apply else 'SIMULACIÓN (no escribe; usa --apply)'
    out('{} | raíz: {} | lado máx: {} px | calidad JPEG: {}'.format(
        mode, root, args.max_side, args.quality))

    scanned = changed = skipped = errors = 0
    before = after = 0
    started = time.time()
    try:
        for path, fmt in iter_files(root, args.only):
            if args.limit and changed >= args.limit:
                break
            scanned += 1
            try:
                content, result = normalize(path, fmt, args.max_side, args.quality)
                size = os.path.getsize(path)
                if content is None:
                    if result != 'ya normalizada':
                        skipped += 1
                        if args.verbose:
                            out('  omitida ({}): {}'.format(result, path))
                    continue
                # Oversized files are replaced whenever they don't grow: the dimensions are
                # what costs decoding time. Orientation-only fixes must save --min-saving.
                limit = size if result else size * (1 - args.min_saving / 100)
                if len(content) > limit:
                    skipped += 1
                    if args.verbose:
                        out('  omitida (no ahorra lo suficiente): {}'.format(path))
                    continue
                if args.apply:
                    backup(path, root, backup_dir, manifest)
                    atomic_replace(path, content)
                changed += 1
                before += size
                after += len(content)
                if args.verbose:
                    out('  {} -> {}  {}'.format(human(size), human(len(content)), path))
            except Exception as e:
                errors += 1
                out('  ERROR {}: {}'.format(path, e))
            if scanned % 500 == 0:
                out('  ... {} revisadas, {} a normalizar, {:.0f}s'.format(
                    scanned, changed, time.time() - started))
    finally:
        if manifest:
            manifest.close()

    out('')
    out('Revisadas: {} | normalizadas{}: {} | omitidas: {} | errores: {}'.format(
        scanned, '' if args.apply else ' (simulado)', changed, skipped, errors))
    out('Tamaño de esas imágenes: {} -> {} (ahorro {})'.format(
        human(before), human(after), human(before - after)))
    out('Tiempo: {:.0f}s'.format(time.time() - started))
    if args.apply:
        out('Respaldo: {} (restaurar con --restore {})'.format(backup_dir, backup_dir))
    return 1 if errors else 0


def restore(args):
    root = os.path.abspath(args.root)
    backup_dir = os.path.abspath(args.restore)
    manifest_path = os.path.join(backup_dir, MANIFEST)
    if not os.path.exists(manifest_path):
        out('No se encontró {}'.format(manifest_path))
        return 1
    restored = errors = 0
    with io.open(manifest_path, 'r', encoding='utf-8') as manifest:
        for line in manifest:
            rel = line.strip()
            if not rel:
                continue
            try:
                source = os.path.join(backup_dir, rel)
                with open(source, 'rb') as f:
                    atomic_replace(os.path.join(root, rel), f.read())
                restored += 1
            except Exception as e:
                errors += 1
                out('  ERROR {}: {}'.format(rel, e))
    out('Restauradas: {} | errores: {}'.format(restored, errors))
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description='Normaliza imágenes antiguas de resources/images')
    parser.add_argument('--root', default=ROOT_DEFAULT, help='directorio de imágenes')
    parser.add_argument('--only', help='subcarpeta dentro de --root (p. ej. peca_project)')
    parser.add_argument('--max-side', type=int, default=MAX_SIDE_DEFAULT)
    parser.add_argument('--quality', type=int, default=QUALITY_DEFAULT)
    parser.add_argument('--min-saving', type=float, default=10,
                        help='ahorro mínimo en %% para reemplazar una imagen que solo '
                             'necesita corregir su orientación')
    parser.add_argument('--limit', type=int, default=0,
                        help='máximo de imágenes a normalizar (0 = todas)')
    parser.add_argument('--apply', action='store_true', help='escribe los cambios')
    parser.add_argument('--backup-dir', help='obligatorio con --apply')
    parser.add_argument('--restore', metavar='BACKUP_DIR', help='revierte un --apply')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    if args.restore:
        return restore(args)
    if args.apply and not args.backup_dir:
        parser.error('--apply requiere --backup-dir')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
