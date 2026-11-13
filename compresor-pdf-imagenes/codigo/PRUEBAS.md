# Ejecutar las pruebas del motor en Linux

Copia `test_optimizer.py` junto a `optimizer.py`. Crea un entorno virtual e instala `pikepdf==10.18.1`, `Pillow==13.0.0` y `pymupdf`. Ejecuta `python test_optimizer.py`. Las pruebas generan sus propios PDF temporales y no necesitan documentos personales.

`build.py` reconstruye el paquete portable de Windows a partir de los archivos oficiales enumerados y verificados por SHA-256 en `manifest.json`. Necesita Python y `ziglang==0.17.1` en el equipo de compilación. Estos requisitos no se aplican al usuario del ZIP portable.
