let
    Origen = Excel.Workbook(File.Contents("Z:\Adiv Puente\CS_AVANCE_AS.xlsx"), null, true),
    Datos = Origen{[Item="HistorialEquipo",Kind="Table"]}[Data],
    // También acepta la cabecera anterior para no romper copias anteriores del Excel.
    Recaudo = if Table.HasColumns(Datos, "RECAUDO") then Datos
        else Table.RenameColumns(Datos, {{"RECUPERO", "RECAUDO"}}),
    Tipos = Table.TransformColumnTypes(Recaudo, {{"FECHA", type date}, {"EQUIPO", type text}, {"RECAUDO", Currency.Type}, {"ALCANCE", Percentage.Type}}),
    Equipos = Table.TransformColumns(Tipos, {{"EQUIPO", each if _ = null then null else Text.Upper(Text.Trim(_)), type nullable text}}),
    Filas = Table.SelectRows(Equipos, each [FECHA] <> null and [EQUIPO] <> null and [EQUIPO] <> ""),
    Conteos = Table.Group(Filas, {"EQUIPO", "FECHA"}, {{"Cantidad", each Table.RowCount(_), Int64.Type}}),
    Resultado = if Table.RowCount(Table.SelectRows(Conteos, each [Cantidad] > 1)) > 0
        then error "HistorialEquipo contiene más de una fila para el mismo equipo y fecha."
        else Filas
in
    Resultado