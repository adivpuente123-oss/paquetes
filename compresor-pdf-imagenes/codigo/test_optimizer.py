from pathlib import Path
import hashlib
import io
import tempfile
import zlib
import pymupdf as fitz
import pikepdf as p
from PIL import Image, ImageDraw
from optimizer import optimize, Omitted

def images(document):
    return [o for o in document.objects if isinstance(o, p.Stream) and o.get('/Subtype') == p.Name.Image]

def drawing_bytes(document):
    return [page.Contents.read_bytes() for page in document.pages]

def make_image(document, data, width, height):
    obj = document.make_stream(data)
    obj.Type=p.Name.XObject;obj.Subtype=p.Name.Image
    obj.Width=width;obj.Height=height;obj.BitsPerComponent=8
    obj.ColorSpace=p.Name.DeviceRGB;obj.Filter=p.Name.FlateDecode
    return obj

with tempfile.TemporaryDirectory(prefix='pdf-images-tests-') as temp:
    root=Path(temp)
    with Image.new('RGB', (4194,2767)) as im:
        draw=ImageDraw.Draw(im)
        for y in range(0,2767,64):
            for x in range(0,4194,64):
                draw.rectangle((x,y,x+63,y+63),fill=((x//64*17+y//64*7)%256,(y//64*23)%256,(x//64*11)%256))
        encoded=zlib.compress(im.tobytes(),9)
    doc=p.Pdf.new()
    font=doc.make_indirect(p.Dictionary(Type=p.Name.Font,Subtype=p.Name.Type1,BaseFont=p.Name.Helvetica))
    for i in range(18):
        page=doc.add_blank_page(page_size=(612,792))
        image=make_image(doc,encoded,4194,2767)
        page.Resources=p.Dictionary(XObject=p.Dictionary(Bg=image),Font=p.Dictionary(F1=font))
        page.Contents=doc.make_stream(f'q 612 0 0 404 0 388 cm /Bg Do Q\nBT /F1 15 Tf 30 350 Td (Pagina {i+1}: texto seleccionable 12345) Tj ET\n0 0 1 RG 30 250 200 50 re S\n'.encode())
    doc.docinfo['/Title']='18 fondos duplicados'
    doc.attachments['prueba.txt']=b'adjunto intacto'
    source=root/'18 fondos.pdf'
    doc.save(source,compress_streams=True)
    digest=hashlib.sha256(source.read_bytes()).digest()
    with p.open(source) as original:
        assert len(images(original))==18
        content=drawing_bytes(original)
    lossless=optimize(source)
    assert lossless['duplicados']==17 and lossless['reducidas']==0 and lossless['archivo']
    with p.open(lossless['archivo']) as output:
        assert len(images(output))==1
        assert int(images(output)[0].Width)==4194
        assert drawing_bytes(output)==content
        assert output.attachments['prueba.txt'].get_file().read_bytes()==b'adjunto intacto'
    with fitz.open(source) as original,fitz.open(lossless['archivo']) as output:
        for a,b in zip(original,output):
            assert a.get_pixmap().samples==b.get_pixmap().samples
            assert a.get_text()==b.get_text()
    print('PASS: 18 imagenes identicas -> 1; render de las 18 paginas pixel por pixel identico; texto, vectores y adjunto intactos')
    resized=optimize(source,1800)
    assert resized['duplicados']==17 and resized['reducidas']==1
    with p.open(resized['archivo']) as output:
        assert len(images(output))==1 and int(images(output)[0].Width)==1800
        assert int(images(output)[0].Height)==1188
        assert drawing_bytes(output)==content
    with fitz.open(source) as original,fitz.open(resized['archivo']) as output:
        assert [x.get_text() for x in original]==[x.get_text() for x in output]
    assert hashlib.sha256(source.read_bytes()).digest()==digest
    second=optimize(source)
    assert second['archivo']!=lossless['archivo'] and Path(lossless['archivo']).exists()
    print('PASS: modo 1800 px, proporcion correcta, una sola imagen reducida; texto seleccionable e instrucciones vectoriales identicos; originales y copias anteriores conservados')
    different=p.Pdf.new()
    for i in range(2):
        page=different.add_blank_page()
        image=make_image(different,encoded,4194,2767)
        if i:
            image.Decode=p.Array([1,0,1,0,1,0])
        page.Resources=p.Dictionary(XObject=p.Dictionary(Bg=image))
        page.Contents=different.make_stream(b'q 500 0 0 330 0 0 cm /Bg Do Q')
    other=root/'atributos diferentes.pdf';different.save(other)
    result=optimize(other)
    assert result['duplicados']==0
    if result['archivo']:
        with p.open(result['archivo']) as output:assert len(images(output))==2
    print('PASS: imagenes con los mismos bytes y distinta interpretacion de colores NO se fusionan')
    masked=p.Pdf.new();page=masked.add_blank_page()
    background=make_image(masked,encoded,4194,2767)
    mask=masked.make_stream(zlib.compress(b'\x80'*(4194*2767),9))
    mask.Type=p.Name.XObject;mask.Subtype=p.Name.Image;mask.Width=4194;mask.Height=2767
    mask.ColorSpace=p.Name.DeviceGray;mask.BitsPerComponent=8;mask.Filter=p.Name.FlateDecode
    background.SMask=mask
    page.Resources=p.Dictionary(XObject=p.Dictionary(Bg=background))
    page.Contents=masked.make_stream(b'q 500 0 0 330 0 0 cm /Bg Do Q')
    other=root/'transparencia.pdf';masked.save(other)
    result=optimize(other,1800)
    assert result['reducidas']==0
    print('PASS: transparencias y sus mascaras conservadas sin reducir')
    signed=root/'firma.pdf'
    with p.open(source) as d:
        d.Root.AcroForm=p.Dictionary(Fields=[d.make_indirect(p.Dictionary(FT=p.Name.Sig,T=p.String('firma')))])
        d.save(signed)
    try:optimize(signed)
    except Omitted:pass
    else:raise AssertionError('No se omitio un campo de firma')
    encrypted=root/'cifrado.pdf'
    with p.open(source) as d:d.save(encrypted,encryption=p.Encryption(user='clave',owner='owner',R=6))
    try:optimize(encrypted)
    except (Omitted,p.PasswordError):pass
    else:raise AssertionError('No se omitio un PDF cifrado')
    print('PASS: campos de firma y PDF cifrados omitidos')
    print(f"Prueba sintetica: {source.stat().st_size} -> {lossless['despues']} bytes sin perdida; {resized['despues']} bytes a 1800 px. No predice la reduccion de otros PDF.")
print('Motor probado en Linux. Lanzador y runtime Windows preparados, sin ejecucion en Windows en este entorno.')
