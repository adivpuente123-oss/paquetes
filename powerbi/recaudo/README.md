# Actualización a RECAUDO — noviembre de 2026

Archivo: `Indicadores_TV_DWH_recaudo_v3.pbix`.

Se parte del PBIX de la release `bimago`, actualizado el 27/11/2026, y del Excel adjuntado en la conversación. Se conserva el PBIX original.

## Cambios

- `HistorialEquipo` lee la cabecera `RECAUDO`. Admite también una copia anterior del Excel con `RECUPERO`.
- El campo acumulado del modelo se llama `RECAUDO`, tanto en `HistorialEquipo` como en la consulta derivada `RecuperoDiario`.
- El cálculo diario sigue restando el cierre del día anterior. Conserva los nombres de salida `RECUPERO_DIARIO` y `RECUPERO_ANTERIOR` para mantener los gráficos existentes. Conserva los negativos y deja vacío cuando falta la base de comparación. El reinicio mensual sigue en `POR_CONFIRMAR`, igual que en el original.
- La consulta de asesores no requiere `%DTO`: se mantiene únicamente un campo interno vacío y oculto por compatibilidad. La medida `% Descuento` queda oculta y vacía.
- Los errores de celda del Excel, incluidos los `#N/A` de META en las personas nuevas sin asignación, se cargan como nulos. No se asignan metas ni equipos inventados.
- Las tarjetas de recaudo utilizan el último acumulado de cada equipo en el mes seleccionado. No suman los recuperos de asesores ni supervisores al acumulado histórico.
- `Alcance total equipo` divide ese recaudo entre la meta oficial del equipo y mes; ya no queda fijado a noviembre de 2026.
- El gráfico de ALCANCE utiliza el alcance del último corte disponible, en vez del máximo porcentaje de todos los cortes.
- Los detalles individuales siguen mostrando el recupero de cada asesor. Su suma puede diferir del recaudo del equipo porque el histórico incluye a los supervisores.
- Se conservan las 22 páginas, fondos, imágenes, colores y posiciones. Solo se cambia el título de las tarjetas de recupero a recaudo y sus referencias de datos.

## Abrir y actualizar

1. Guardar una copia del Excel actualizado en la ruta ya configurada: `Z:\Adiv Puente\CS_AVANCE_AS.xlsx`.
2. Abrir el nuevo PBIX en Power BI Desktop.
3. Ejecutar **Actualizar** desde el equipo con acceso a la unidad Z:, al archivo de condonaciones y al SQL corporativo.
4. Comprobar el resultado y guardar el archivo. El PBIX descargado conserva los datos almacenados en la última actualización del original hasta que se actualice.

Con el Excel adjunto, el cierre 26/11/2026 de LISELY es S/ 171,390.90 y aproximadamente 57.91 %. En SANDY el acumulado baja S/ 5,629 ese día; se conserva esa diferencia negativa para reflejar la fuente.

## Alcance de la verificación

Se verificaron ZIP, integridad SQLite, lectura del modelo resultante, consultas, medidas, referencias de todos los visuales, conservación de los recursos y estructura de páginas. Los bytes del modelo descomprimido son idénticos salvo la base de metadatos modificada.

**No se ha abierto ni actualizado este PBIX en Power BI Desktop. Se modificaron sus metadatos fuera de Desktop; la comprobación estructural no certifica que el motor nativo abra, compile o actualice correctamente el archivo. Debe comprobarse en Desktop antes de sustituir el archivo de uso habitual.**

Se incluyen las tres consultas `.pq` y las medidas `.dax` como respaldo para aplicar los mismos cambios desde las herramientas nativas si fuera necesario. `validacion.json` contiene el detalle de las comprobaciones y el SHA-256.
