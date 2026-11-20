let
    RutaExcel = "CAMBIA_POR_LA_RUTA_COMPLETA_DEL_EXCEL",
    ReinicioMensual = "POR_CONFIRMAR",
    Config = if List.Contains({"SI", "NO", "POR_CONFIRMAR"}, ReinicioMensual) then ReinicioMensual else error "ReinicioMensual debe ser SI, NO o POR_CONFIRMAR.",
    Libro = Excel.Workbook(File.Contents(RutaExcel), null, true),
    Origen = Libro{[Item="HistorialEquipo", Kind="Table"]}[Data],
    LimpiarFecha = (valor as any) as nullable date => if valor = null then null else if Value.Is(valor, type text) and Text.Trim(valor) = "" then null else Date.From(valor),
    Fechas = Table.TransformColumns(Origen, {{"FECHA", LimpiarFecha, type nullable date}}),
    Equipos = Table.TransformColumns(Fechas, {{"EQUIPO", each if _ = null then null else Text.Upper(Text.Trim(Text.From(_))), type nullable text}}),
    ConFechaEquipo = Table.SelectRows(Equipos, each [FECHA] <> null and [EQUIPO] <> null and [EQUIPO] <> ""),
    Conteos = Table.Group(ConFechaEquipo, {"EQUIPO", "FECHA"}, {{"Filas", each Table.RowCount(_), Int64.Type}}),
    Unicos = if Table.RowCount(Table.SelectRows(Conteos, each [Filas] > 1)) > 0 then error "Hay equipos y fechas duplicados. Corrigelos antes de actualizar." else ConFechaEquipo,
    Importes = Table.AddColumn(Unicos, "ACUMULADO_NUM", each if Value.Is([RECUPERO], type number) then Number.From([RECUPERO]) else null, type nullable number),
    DiaPrevio = Table.AddColumn(Importes, "FECHA_ANTERIOR", each Date.AddDays([FECHA], -1), type date),
    Cruce = Table.NestedJoin(DiaPrevio, {"EQUIPO", "FECHA_ANTERIOR"}, Importes, {"EQUIPO", "FECHA"}, "Previo", JoinKind.LeftOuter),
    Previo = Table.ExpandTableColumn(Cruce, "Previo", {"ACUMULADO_NUM"}, {"ACUMULADO_ANTERIOR"}),
    Base = Table.AddColumn(Previo, "BASE_COMPARACION", each if Date.Day([FECHA]) = 1 then if Config = "SI" then 0 else if Config = "NO" then [ACUMULADO_ANTERIOR] else null else [ACUMULADO_ANTERIOR], type nullable number),
    Diario = Table.AddColumn(Base, "RECUPERO_DIARIO", each if [ACUMULADO_NUM] = null or [BASE_COMPARACION] = null then null else [ACUMULADO_NUM] - [BASE_COMPARACION], type nullable number),
    Control = Table.AddColumn(Diario, "CONTROL_DIARIO", each if [ACUMULADO_NUM] = null then "ACUMULADO NO NUMERICO" else if Date.Day([FECHA]) = 1 and Config = "POR_CONFIRMAR" then "CONFIRMAR REINICIO MENSUAL" else if [BASE_COMPARACION] = null then "SIN CORTE ANTERIOR CONSECUTIVO" else if [RECUPERO_DIARIO] < 0 then "AJUSTE NEGATIVO: REVISAR" else "OK", type text),
    Periodo = Table.AddColumn(Control, "PERIODO", each Date.StartOfMonth([FECHA]), type date),
    Limpiar = Table.RemoveColumns(Periodo, {"FECHA_ANTERIOR"}),
    Orden = Table.Sort(Limpiar, {{"EQUIPO", Order.Ascending}, {"FECHA", Order.Ascending}})
in
    Orden
