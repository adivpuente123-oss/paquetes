let
    Origen = Excel.Workbook(File.Contents("Z:\Adiv Puente\CS_AVANCE_AS.xlsx"), null, true),
    Datos = Origen{[Item="D1_JULIO_2026",Kind="Table"]}[Data],
    // Excel puede incluir personas nuevas cuya META todavía devuelve #N/A.
    SinErrores = Table.ReplaceErrorValues(Datos, List.Transform(Table.ColumnNames(Datos), each {_, null})),
    Equipo = Table.RenameColumns(SinErrores, {{"SUPER2", "Equipo"}}),
    Nombres = Table.TransformColumns(Equipo, {
        {"ASESOR_CRR", each if _ = null then null else Text.Trim(Text.From(_)), type nullable text},
        {"Equipo", each if _ = null then null else Text.Upper(Text.Trim(Text.From(_))), type nullable text}
    }),
    Personas = Table.SelectRows(Nombres, each [ASESOR_CRR] <> null and [ASESOR_CRR] <> ""),
    // Campo interno vacío de compatibilidad; %DTO ya no se lee ni se utiliza.
    SinDescuento = Table.RemoveColumns(Personas, {"%DTO"}, MissingField.Ignore),
    Compatibilidad = Table.AddColumn(SinDescuento, "%DTO", each null, type nullable number),
    Tipos = Table.TransformColumnTypes(Compatibilidad, {{"ALCANCE", Percentage.Type}, {"RECUPERO", type number}}),
    Resultado = Table.AddColumn(Tipos, "ClaveAsesor", each Text.Upper(Text.Trim(Text.Clean([ASESOR_CRR]))), type text)
in
    Resultado