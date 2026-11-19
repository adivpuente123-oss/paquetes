let
    // Usa aqui la misma ruta del Excel que ya utilizaba tu consulta original.
    RutaExcel = "CAMBIA_POR_LA_RUTA_COMPLETA_DEL_EXCEL",
    Libro = Excel.Workbook(File.Contents(RutaExcel), null, true),
    Tabla = Libro{[Item = "D1_JULIO_2026", Kind = "Table"]}[Data],
    Equipo = Table.RenameColumns(Tabla, {{"SUPER2", "Equipo"}}),
    FechaONull = (valor as any) as nullable date => if valor = null then null else if Value.Is(valor, type text) and Text.Trim(valor) = "" then null else Date.From(valor),
    Fechas = Table.TransformColumns(Equipo, {{"FECHA_RECEPCION", FechaONull, type nullable date}, {"FECHA_CORTE", FechaONull, type nullable date}}),
    Tipos = Table.TransformColumnTypes(Fechas, {{"ALCANCE", Percentage.Type}}),
    Identificador = Table.TransformColumns(Tipos, {{"DNI", each if _ = null or Text.Trim(Text.From(_)) = "" then null else Text.PadStart(Text.Trim(Text.From(_)), 8, "0"), type nullable text}}),
    Corte = Table.AddColumn(Identificador, "CORTE_VALIDADO", each if [FECHA_CORTE] <> null then [FECHA_CORTE] else if [FECHA_RECEPCION] <> null then Date.AddDays([FECHA_RECEPCION], -1) else null, type nullable date),
    SinCorteAnterior = Table.RemoveColumns(Corte, {"FECHA_CORTE"}),
    NombreCorte = Table.RenameColumns(SinCorteAnterior, {{"CORTE_VALIDADO", "FECHA_CORTE"}}),
    Numero = Table.AddColumn(NombreCorte, "ACUMULADO_NUM", each if Value.Is([RECUPERO], type number) then Number.From([RECUPERO]) else null, type nullable number)
in
    Numero
