# Paquetes

## Compresor PDF sin pérdida 1.2 para Windows x64

[**Descargar CompresorPDF_Windows_x64.zip**](https://github.com/adivpuente123-oss/paquetes/raw/refs/heads/main/compresor-pdf/CompresorPDF_Windows_x64.zip)

1. Descarga y extrae el ZIP.
2. Abre `CompresorPDF.exe`. No requiere instalación ni Python.
3. Selecciona uno o varios PDF. También puedes arrastrarlos sobre el ejecutable.
4. La copia `nombre_comprimido.pdf` se guarda junto al original si pesa menos.

Conserva los originales. No reduce la resolución de imágenes ni recomprime JPEG con pérdida. La reducción depende del archivo: un PDF optimizado puede no reducirse. Los archivos se procesan localmente y no se suben a Internet.

La compresión cambia la estructura y los bytes del PDF; mantiene su contenido y calidad visual. No conserva la linearización y no se certifica conformidad PDF/A. Los PDF cifrados o con campos de firma digital se omiten.

### Avisos de integridad y carga rápida web

La versión 1.2 permite continuar si todos los avisos del chequeo de entrada corresponden a los cuatro patrones de tablas de carga rápida web enumerados en las instrucciones. La copia se escribe sin linearización y debe pasar la verificación de integridad sin avisos. Los avisos de referencias cruzadas, los errores de datos y los avisos desconocidos siguen bloqueándose.

Si se bloquea un archivo, se muestra el detalle y se guarda `nombre.pdf_diagnostico.txt` junto al PDF.

### Validación

Motor qpdf probado en Linux con texto, JPEG, formularios, enlaces, metadatos y adjuntos. Se probó un PDF con una tabla de carga rápida web inconsistente: ambas compresiones producen copias sin avisos y con contenido lógico idéntico. También se comprueba el rechazo de avisos estructurales y mixtos. El ejecutable se compiló para Windows x64 con avisos del compilador tratados como errores; la interfaz de Windows no se ejecutó en este entorno.

- [Instrucciones completas](compresor-pdf/LEEME.txt)
- [Código fuente y compilación](compresor-pdf/codigo/)
- [Pruebas realizadas](compresor-pdf/PRUEBAS.txt)
- [Licencias](compresor-pdf/licencias/)
