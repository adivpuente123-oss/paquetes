# Excel con una sola tabla de origen

Archivo: **CS_AVANCE_AS_solo_D1.xlsx**.

No se agregaron hojas. Se conservaron las ocho existentes y las otras tablas. La tabla **D1_JULIO_2026**, de **NOVIEMBRE_2026**, pasa de A2:L51 a **A7:N56**: se mueve cinco filas para conservar en N2:P3 los controles de año, mes y días laborables. Las referencias relativas de sus fórmulas se trasladan y las referencias absolutas a esos controles permanecen iguales.

Se mantienen sus doce columnas y se añaden solo dos al final:

- **M: FECHA_RECEPCION**, que debes escribir como fecha fija.
- **N: FECHA_CORTE**, calculada como recepción menos un día. Si un reporte llega con retraso, corrige la fecha de corte para reflejar la fecha real, no una fecha supuesta.

No se asignó fecha a los valores actuales. No se crearon datos históricos ni se modificó el PBIX.

## Antes de incorporar varios días: ajustar Power Query

**No acumules nuevos cortes y actualices el BI con la consulta anterior sin filtrar: sumaría acumulados de fechas distintas.** Haz una copia de seguridad del Excel y del PBIX.

1. Guarda el nuevo Excel en una ruta elegida. Puedes conservar el nombre y ruta del archivo original, después de hacer el respaldo, para mantener las otras conexiones existentes.
2. En Power BI, abre **Transformar datos → Nueva fuente → Consulta en blanco → Editor avanzado**. Crea **BaseRecupero** con el contenido de `01_BaseRecupero.pq`. Cambia únicamente `RutaExcel` por la ruta completa del Excel nuevo. Deshabilita su carga: será una consulta auxiliar.
3. Crea otra consulta en blanco llamada **HistorialRecupero** con `02_HistorialRecupero.pq`. Cambia `ReinicioMensual` a `"SI"` si el acumulado se reinicia a cero cada mes, o a `"NO"` si continúa. Por defecto se deja `"POR_CONFIRMAR"`: calcula dentro del mes, pero no calcula el día 1 hasta que confirmes esa regla.
4. Abre la consulta existente **D1_MAYO_2026** y guarda una copia de su código en un archivo de texto. Sustituye su código por `03_D1_MAYO_2026_ultimo_corte.pq`. **No cambies el nombre de esa consulta ni elimines la tabla del modelo.** Los gráficos actuales mantendrán sus referencias, pero leerán únicamente el último cierre disponible. Mientras no hayas fechado ningún registro, se conserva el contenido original.
5. Cierra y aplica; compara los importes de los indicadores con el cierre original antes de continuar. El código M se entrega para aplicarlo en Desktop; no se ha ejecutado en este entorno.

## Registro de cada cierre

- Un corte debe incluir a todos los asesores que correspondan al equipo/cartera que estás reportando; guarda el lote completo antes de actualizar Power BI. La consulta actual utiliza la última fecha global, no una mezcla de fechas distintas por asesor.
- Para el primer corte, completa **FECHA_RECEPCION** únicamente en las filas cuyos acumulados correspondan realmente a ese cierre. No uses `HOY()` ni fechas supuestas.
- Para cada día siguiente, **añade nuevas filas al final de la misma tabla**, con una fila por asesor. No reemplaces los recuperos de los días anteriores. Amplía la tabla usando Tab en su última celda o escribiendo inmediatamente debajo.
- Cada fila fechada debe ser una fotografía fija: en las columnas **A:L** usa **Pegado especial → Valores** para conservar equipo, meta, descuento e importe de ese corte, en lugar de fórmulas que cambien al modificar el mes o el padrón. Al archivar el primer corte, congela también A:L de ese bloque. La fórmula de FECHA_CORTE puede permanecer.
- Para el nuevo bloque, copia como valores los datos vigentes del asesor, actualiza RECUPERO y los demás datos que hayan cambiado y escribe FECHA_RECEPCION. Mantén DNI como texto y conserva los ceros iniciales.
- Registra solo acumulados por asesor. No agregues subtotales de supervisores que ya incluyen el importe de sus asesores. Si una cartera se informa por separado, no mezcles dos acumulados de carteras distintas bajo el mismo DNI y fecha: habría que incorporar esa clave en las consultas.

## Cálculo diario

Se calcula en **HistorialRecupero**, sin otra hoja de Excel. Busca el acumulado del mismo DNI con cierre exactamente un día anterior. Si falta ese corte, deja RECUPERO_DIARIO vacío: una diferencia de varios días no se atribuye a uno solo. Las filas duplicadas producen un error de actualización para que se corrijan.

Ejemplo ficticio: recibido 18/11, cierre 17/11, acumulado 5,600; recibido 19/11, cierre 18/11, acumulado 6,100. Resultado: **500 para el 18/11**.

Los negativos se mantienen como ajustes y se señalan. Los textos o vacíos no se convierten en cero. El primer registro a mitad de mes necesita un corte previo para producir un diario.

## Gráfico

Crea la medida:

```DAX
Recupero diario cartera =
SUM('HistorialRecupero'[RECUPERO_DIARIO])
```

Usa **FECHA_CORTE** como eje X. Relaciona el historial con un calendario y una dimensión de asesores con DNI único; evita unir directamente dos tablas con muchos registros por DNI. Para el nuevo historial usa Equipo y las fechas que correspondan al corte. No relaciones el histórico solo con D1_MAYO_2026 como si fuera un padrón histórico: esa tabla muestra únicamente el último corte.

El Excel y la estructura del código se validan por separado. La apertura/actualización de este PBIX con las consultas nuevas debe revisarse en Power BI Desktop. No se modificaron automáticamente las consultas dentro del PBIX.
