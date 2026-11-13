# Paquetes

## Compresor PDF sin pérdida 1.1 para Windows x64

[**Descargar CompresorPDF_Windows_x64.zip**](https://github.com/adivpuente123-oss/paquetes/raw/refs/heads/main/compresor-pdf/CompresorPDF_Windows_x64.zip)

1. Descarga y extrae el ZIP.
2. Abre `CompresorPDF.exe`. No requiere instalación ni Python.
3. Selecciona uno o varios PDF. También puedes arrastrarlos sobre el ejecutable.
4. La copia `nombre_comprimido.pdf` se guarda junto al original si pesa menos.

Conserva los originales. No reduce la resolución de imágenes ni recomprime JPEG con pérdida. Omite PDF cifrados, con campos de firma digital o con errores. La reducción depende del archivo: un PDF optimizado puede no reducirse. Los archivos se procesan localmente y no se suben a Internet.

La compresión cambia la estructura y los bytes del PDF; mantiene su contenido y calidad visual. No conserva necesariamente la linearización y no se certifica conformidad PDF/A.

Motor qpdf probado en Linux con texto, JPEG, formularios, enlaces, metadatos y adjuntos. El ejecutable se compiló para Windows x64, pero la interfaz de Windows no se ejecutó en este entorno.

- [Instrucciones completas](compresor-pdf/LEEME.txt)
- [Código fuente y compilación](compresor-pdf/codigo/)
- [Pruebas realizadas](compresor-pdf/PRUEBAS.txt)
- [Licencias](compresor-pdf/licencias/)

### Versión 1.1: diagnóstico de avisos

Si qpdf emite avisos o errores, el programa muestra el detalle y guarda `nombre.pdf_diagnostico.txt` junto al PDF. El código 3 identifica avisos y no implica necesariamente que el documento sea ilegible. Comparte el diagnóstico para determinar si es posible tratarlo sin cambiar el contenido; el programa no lo repara automáticamente.
