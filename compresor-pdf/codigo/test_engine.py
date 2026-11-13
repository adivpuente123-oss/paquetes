from pathlib import Path
import hashlib, io, json, re, subprocess, zlib
import pikepdf as p
from PIL import Image

ROOT = Path(__file__).parent
QPDF = ROOT / 'linux/bin/qpdf'
TMP = ROOT / 'tests'
TMP.mkdir(exist_ok=True)

def run(*args, expected=0):
    r = subprocess.run([str(QPDF), *map(str, args)], capture_output=True)
    assert r.returncode == expected, (args, r.returncode, r.stderr.decode(errors='replace'))
    return r.stdout

def canonical(obj, seen=None):
    if seen is None:
        seen = {}
    if isinstance(obj, p.Object) and obj.is_indirect:
        key = obj.objgen
        if key in seen:
            return ['ref', seen[key]]
        seen[key] = len(seen)
    if isinstance(obj, p.Stream):
        try:
            content = obj.read_bytes()
            omitted = {'/Length', '/Filter', '/DecodeParms'}
        except p.PdfError:
            content = obj.read_raw_bytes()
            omitted = {'/Length'}
        return ['stream', hashlib.sha256(content).hexdigest(),
                [(k, canonical(obj[k], seen)) for k in sorted(obj.keys()) if k not in omitted]]
    if isinstance(obj, p.Dictionary):
        return ['dict', [(k, canonical(obj[k], seen)) for k in sorted(obj.keys())]]
    if isinstance(obj, p.Array):
        return ['array', [canonical(x, seen) for x in obj]]
    if isinstance(obj, p.String):
        return ['string', bytes(obj).hex()]
    return str(obj)

doc = p.Pdf.new()
page = doc.add_blank_page(page_size=(612, 792))
font = doc.make_indirect(p.Dictionary(Type=p.Name.Font, Subtype=p.Name.Type1, BaseFont=p.Name.Helvetica))
page.Resources = p.Dictionary(Font=p.Dictionary(F1=font))
page.Contents = doc.make_stream((b'BT /F1 14 Tf 50 700 Td (Prueba sin perdida) Tj ET\n' + b'% comentario preservado\n' * 16000))
imgbuf = io.BytesIO()
Image.new('RGB', (64, 64), (52, 120, 180)).save(imgbuf, format='JPEG', quality=97)
image = doc.make_stream(imgbuf.getvalue())
image.Type=p.Name.XObject; image.Subtype=p.Name.Image
image.Width=64; image.Height=64; image.ColorSpace=p.Name.DeviceRGB; image.BitsPerComponent=8
image.Filter=p.Name.DCTDecode
page.Resources.XObject=p.Dictionary(Im1=image)
link=doc.make_indirect(p.Dictionary(Type=p.Name.Annot,Subtype=p.Name.Link,Rect=[10,10,100,30],A=p.Dictionary(S=p.Name.URI,URI=p.String('https://example.com'))))
field=doc.make_indirect(p.Dictionary(Type=p.Name.Annot,Subtype=p.Name.Widget,FT=p.Name.Tx,T=p.String('nombre'),V=p.String('María'),Rect=[50,500,250,530]))
page.Annots=p.Array([link,field]);doc.Root.AcroForm=p.Dictionary(Fields=[field],NeedAppearances=True)
doc.docinfo['/Title']='Documento de prueba';doc.docinfo['/Author']='Verificación'
doc.Root.Metadata=doc.make_stream(b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:format>application/pdf</dc:format></rdf:Description></rdf:RDF></x:xmpmeta>')
doc.Root.Metadata.Type=p.Name.Metadata;doc.Root.Metadata.Subtype=p.Name.XML
doc.attachments['anexo.txt']=b'Anexo sin modificar\x00\xff\n'
source=TMP/'ejemplo con espacios y ñ.pdf'
doc.save(source,compress_streams=False,object_stream_mode=p.ObjectStreamMode.disable)
baseline=hashlib.sha256(source.read_bytes()).hexdigest()
reference=(canonical(doc.Root), canonical(doc.docinfo))
sizes=[]
for mode in ('preserve','disable'):
    output=TMP/f'{mode}.pdf'
    run(f'--object-streams={mode}','--compress-streams=y','--decode-level=generalized','--recompress-flate','--compression-level=9','--preserve-unreferenced',source,output)
    run('--check',output)
    with p.open(output) as opt:
        assert (canonical(opt.Root),canonical(opt.docinfo))==reference, 'Cambió el contenido lógico'
        assert len(opt.pages)==1
        assert opt.pdf_version == doc.pdf_version
        assert opt.pages[0].Resources.XObject.Im1.read_raw_bytes()==imgbuf.getvalue()
        assert opt.attachments['anexo.txt'].get_file().read_bytes()==b'Anexo sin modificar\x00\xff\n'
    sizes.append(output.stat().st_size)
    print(f'PASS {mode}: {source.stat().st_size} -> {sizes[-1]} bytes; contenido lógico, JPEG, formulario, enlaces, metadatos y adjuntos idénticos')
assert min(sizes)<source.stat().st_size
assert hashlib.sha256(source.read_bytes()).hexdigest()==baseline
run('--is-encrypted',source,expected=2)
encrypted=TMP/'encrypted.pdf'
with p.open(source) as d:
    d.save(encrypted,encryption=p.Encryption(owner='owner',user='secret',R=6))
run('--is-encrypted',encrypted,expected=0)
print('PASS detección de cifrado y original intacto')
signed=TMP/'signature.pdf'
with p.open(source) as d:
    d.Root.AcroForm.Fields.append(d.make_indirect(p.Dictionary(FT=p.Name.Sig,T=p.String('firma'),V=p.Dictionary(Type=p.Name.Sig,ByteRange=[0,10,20,30],Contents=p.String(b'placeholder')))))
    d.save(signed,object_stream_mode=p.ObjectStreamMode.generate)
data=run('--json','--json-key=qpdf','--json-stream-data=none',signed)
assert b'"/ByteRange"' in data and b'"/Sig"' in data
print('PASS detección de campos de firma en objetos comprimidos')
warning=TMP/'xref-warning.pdf'
warning.write_bytes(re.sub(rb'startxref\s+\d+',b'startxref\n1',source.read_bytes()))
before=hashlib.sha256(warning.read_bytes()).digest()
result=subprocess.run([str(QPDF),'--check',str(warning)],capture_output=True)
assert result.returncode==3 and b'WARNING' in result.stderr
assert b'cross-reference' in result.stderr or b'startxref' in result.stderr
assert hashlib.sha256(warning.read_bytes()).digest()==before
print('PASS aviso recuperable: código 3, detalle de referencias cruzadas disponible y original intacto')
classifier=ROOT/'test_warnings'
subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/'test_warnings.c'),'-o',str(classifier)],check=True)
subprocess.run([str(classifier)],check=True)
linearized=TMP/'linearized.pdf'
run('--linearize',source,linearized)
data=linearized.read_bytes()
hint=re.search(rb'/H\s*\[\s*(\d+)\s+(\d+)',data)
offset=int(hint[1]);block=data[offset:offset+int(hint[2])]
stream=re.search(rb'stream\r?\n(.*?)\r?\nendstream',block,re.S)
raw=bytearray(zlib.decompress(stream[1]))
raw[:4]=(int.from_bytes(raw[:4],'big')-1).to_bytes(4,'big')
faulty=TMP/'hints-warning.pdf'
def write_hint_fixture():
    compressed=zlib.compress(raw)
    assert len(compressed)<=len(stream[1])
    compressed+=b'\0'*(len(stream[1])-len(compressed))
    pos=offset+stream.start(1)
    faulty.write_bytes(data[:pos]+compressed+data[pos+len(stream[1]):])
write_hint_fixture()
r=subprocess.run([str(QPDF),'--check',str(faulty)],capture_output=True)
computed=re.search(rb'page length mismatch for page 0: hint table = \d+; computed length = (\d+)',r.stderr)
assert computed
raw[10:14]=int(computed[1]).to_bytes(4,'big')
raw[22:26]=int(computed[1]).to_bytes(4,'big')
write_hint_fixture()
r=subprocess.run([str(QPDF),'--check',str(faulty)],capture_output=True)
assert r.returncode==3
log=TMP/'hints-warning.log';log.write_bytes(r.stdout+r.stderr)
subprocess.run([str(classifier),str(log)],check=True)
baseline=hashlib.sha256(faulty.read_bytes()).digest()
with p.open(faulty) as d:
    original_graph=(canonical(d.Root),canonical(d.docinfo))
for mode in ('preserve','disable'):
    output=TMP/f'hints-fixed-{mode}.pdf'
    run(f'--object-streams={mode}','--compress-streams=y','--decode-level=generalized','--recompress-flate','--compression-level=9','--preserve-unreferenced',faulty,output)
    run('--check',output)
    with p.open(output) as d:
        assert (canonical(d.Root),canonical(d.docinfo))==original_graph
        assert d.pdf_version=='1.3'
    assert output.stat().st_size<faulty.stat().st_size
assert hashlib.sha256(faulty.read_bytes()).digest()==baseline
bad=TMP/'structural-warning.log';bad.write_bytes(result.stdout+result.stderr)
assert subprocess.run([str(classifier),str(bad)]).returncode==1
log.write_bytes(log.read_bytes()+result.stderr)
assert subprocess.run([str(classifier),str(log)]).returncode==1
print('PASS PDF con aviso real de hint table: compresión aceptada, ambas copias sin avisos, contenido lógico idéntico y original intacto; reconstrucción xref y avisos mixtos rechazados')
print('Las pruebas ejecutan el motor qpdf en Linux. La interfaz PE de Windows se compila, pero no se ejecuta en este entorno.')
