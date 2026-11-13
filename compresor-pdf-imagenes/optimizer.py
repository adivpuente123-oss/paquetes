"""Portable PDF image optimizer. No rasterization of pages or text."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zlib
import pikepdf as pdf
from PIL import Image

class Omitted(Exception):
    pass

def is_image(obj):
    return isinstance(obj, pdf.Stream) and obj.get('/Subtype') == pdf.Name.Image

def image_key(obj):
    """Compare encoded bytes AND every rendering/metadata attribute, recursively."""
    active = set()
    def node(value):
        key = value.objgen if isinstance(value, pdf.Object) and value.is_indirect else None
        if key in active:
            raise ValueError('Cyclic image attributes')
        if key:
            active.add(key)
        try:
            if isinstance(value, pdf.Stream):
                return ['stream', hashlib.sha256(value.read_raw_bytes()).hexdigest(),
                        [(k, node(value[k])) for k in sorted(value.keys()) if k != '/Length']]
            if isinstance(value, pdf.Dictionary):
                return ['dict', [(k, node(value[k])) for k in sorted(value.keys())]]
            if isinstance(value, pdf.Array):
                return ['array', [node(v) for v in value]]
            if isinstance(value, pdf.String):
                return ['string', bytes(value).hex()]
            return [type(value).__name__, str(value)]
        finally:
            if key:
                active.remove(key)
    return hashlib.sha256(json.dumps(node(obj), ensure_ascii=True).encode()).digest()

def deduplicate(document):
    seen, canonical, replacements = set(), {}, set()
    def walk(obj):
        if not isinstance(obj, (pdf.Dictionary, pdf.Stream, pdf.Array)):
            return obj
        if is_image(obj):
            try:
                key = image_key(obj)
            except (ValueError, pdf.PdfError):
                key = None
            if key is not None:
                previous = canonical.setdefault(key, obj)
                if previous.objgen != obj.objgen:
                    replacements.add(obj.objgen)
                    return previous
        if obj.is_indirect:
            if obj.objgen in seen:
                return obj
            seen.add(obj.objgen)
        if isinstance(obj, pdf.Array):
            for i in range(len(obj)):
                value = obj[i]
                updated = walk(value)
                if isinstance(value, pdf.Object) and value.is_indirect and updated.objgen != value.objgen:
                    obj[i] = updated
        else:
            for key in list(obj.keys()):
                value = obj[key]
                updated = walk(value)
                if isinstance(value, pdf.Object) and value.is_indirect and updated.objgen != value.objgen:
                    obj[key] = updated
        return obj
    walk(document.trailer)
    return list(canonical.values()), len(replacements)

def drawing_streams(document):
    seen, hashes = set(), []
    def walk(obj):
        if not isinstance(obj, (pdf.Stream, pdf.Dictionary, pdf.Array)):
            return
        if obj.is_indirect:
            if obj.objgen in seen:
                return
            seen.add(obj.objgen)
        if isinstance(obj, pdf.Stream):
            if obj.get('/Subtype') == pdf.Name.Form:
                hashes.append(hashlib.sha256(obj.read_bytes()).digest())
            # Image metadata does not contain drawing operators.
            if is_image(obj):
                return
        if isinstance(obj, pdf.Array):
            for child in obj:
                walk(child)
        else:
            for child in obj.values():
                walk(child)
    pages = []
    for page in document.pages:
        contents = page.obj.get('/Contents', pdf.Array())
        if isinstance(contents, pdf.Stream):
            contents = [contents]
        pages.append(tuple(hashlib.sha256(s.read_bytes()).digest() for s in contents))
    walk(document.Root)
    return pages, Counter(hashes)

def resize_image(obj, width, masks):
    if not width or int(obj.get('/Width', 0)) <= width:
        return False
    if obj.objgen in masks or any(k in obj for k in ('/Mask', '/SMask', '/Decode', '/Alternates')):
        return False
    if obj.get('/ImageMask', False) or int(obj.get('/SMaskInData', 0)):
        return False
    if int(obj.get('/BitsPerComponent', 0)) != 8:
        return False
    space = obj.get('/ColorSpace')
    if space not in (pdf.Name.DeviceRGB, pdf.Name.DeviceGray):
        return False
    with pdf.PdfImage(obj).as_pil_image() as image:
        expected = 'RGB' if space == pdf.Name.DeviceRGB else 'L'
        if image.mode != expected:
            return False
        height = max(1, round(image.height * width / image.width))
        with image.resize((width, height), Image.Resampling.LANCZOS) as smaller:
            encoded = zlib.compress(smaller.tobytes(), 9)
        if len(encoded) >= len(obj.read_raw_bytes()):
            return False
    obj.write(encoded, filter=pdf.Name.FlateDecode)
    if '/DecodeParms' in obj:
        del obj['/DecodeParms']
    obj.Width = width
    obj.Height = height
    return True

def optimize(source, width=0):
    source = Path(source).resolve()
    if source.suffix.lower() != '.pdf':
        raise Omitted('Selecciona un archivo PDF.')
    before = source.stat()
    with pdf.Pdf.open(source, attempt_recovery=False) as document:
        if document.is_encrypted:
            raise Omitted('PDF cifrado: no se modifica.')
        warnings = document.get_warnings()
        if warnings:
            raise Omitted('Avisos al leer el PDF: ' + '\n'.join(warnings))
        for obj in document.objects:
            if isinstance(obj, (pdf.Dictionary, pdf.Stream)) and (
                '/ByteRange' in obj or obj.get('/FT') == pdf.Name.Sig or obj.get('/Type') == pdf.Name.Sig
            ):
                raise Omitted('Firma digital o campo de firma: no se modifica.')
        original_drawing = drawing_streams(document)
        # Metadata and attachments must retain their exact decoded bytes.
        metadata = document.Root.get('/Metadata')
        xmp = metadata.read_bytes() if isinstance(metadata, pdf.Stream) else None
        attachments = {name: hashlib.sha256(item.get_file().read_bytes()).digest()
                       for name, item in document.attachments.items()}
        original_info = image_key(document.docinfo)
        masks = set()
        for obj in document.objects:
            if is_image(obj):
                for key in ('/Mask', '/SMask'):
                    mask = obj.get(key)
                    if isinstance(mask, pdf.Stream):
                        masks.add(mask.objgen)
        unique, duplicates = deduplicate(document)
        resized = 0
        for image in unique:
            try:
                resized += resize_image(image, width, masks)
            except (pdf.PdfError, OSError, ValueError) as exc:
                print(f'Imagen conservada sin reducir: {exc}', flush=True)
        if document.get_warnings():
            raise Omitted('El motor emitio avisos al procesar imagenes; se conserva el original.')
        with tempfile.TemporaryDirectory(prefix='pdf-imagenes-', dir=source.parent) as temp:
            candidate = Path(temp) / 'candidate.pdf'
            document.save(candidate, compress_streams=True, recompress_flate=True,
                          object_stream_mode=pdf.ObjectStreamMode.preserve,
                          fix_metadata_version=False, normalize_content=False)
            with pdf.Pdf.open(candidate, attempt_recovery=False) as verified:
                issues = verified.check_pdf_syntax() + verified.get_warnings()
                if issues:
                    raise Omitted('La copia no paso la verificacion: ' + '\n'.join(issues))
                if drawing_streams(verified) != original_drawing:
                    raise Omitted('La copia cambio instrucciones de texto o dibujo; no se guarda.')
                current = verified.Root.get('/Metadata')
                if (current.read_bytes() if isinstance(current, pdf.Stream) else None) != xmp:
                    raise Omitted('La copia cambio metadatos; no se guarda.')
                if image_key(verified.docinfo) != original_info:
                    raise Omitted('La copia cambio propiedades del documento; no se guarda.')
                for name, digest in attachments.items():
                    if hashlib.sha256(verified.attachments[name].get_file().read_bytes()).digest() != digest:
                        raise Omitted('La copia cambio un adjunto; no se guarda.')
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise Omitted('El original cambio durante el proceso; vuelve a intentarlo.')
            result = {'duplicados': duplicates, 'reducidas': resized, 'antes': before.st_size,
                      'despues': candidate.stat().st_size, 'archivo': None}
            if result['despues'] >= result['antes']:
                return result
            suffix = '_imagenes1800' if width else '_sin_duplicados'
            for number in range(1, 10000):
                extra = '' if number == 1 else f' ({number})'
                destination = source.with_name(source.stem + suffix + extra + '.pdf')
                try:
                    target = destination.open('xb')
                except FileExistsError:
                    continue
                try:
                    with target, candidate.open('rb') as data:
                        shutil.copyfileobj(data, target, length=1024 * 1024)
                        target.flush()
                        os.fsync(target.fileno())
                except BaseException:
                    destination.unlink(missing_ok=True)
                    raise
                result['archivo'] = str(destination)
                return result
            raise Omitted('Hay demasiadas copias con el mismo nombre.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--width', type=int, choices=[0, 1800], default=0)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    errors = 0
    for name in args.files:
        print(f'\nArchivo: {name}', flush=True)
        try:
            result = optimize(name, args.width)
            print(f"Copias de imagen eliminadas: {result['duplicados']}; imagenes reducidas: {result['reducidas']}", flush=True)
            if result['archivo']:
                print(f"Guardado: {result['archivo']}\n{result['antes']/1048576:.2f} MB -> {result['despues']/1048576:.2f} MB", flush=True)
            else:
                print('No se consiguio un archivo menor; no se crea copia.', flush=True)
        except Exception as exc:
            print(f'Omitido: {exc}', flush=True)
            errors += 1
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
