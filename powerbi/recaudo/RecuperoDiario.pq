let
    // SI: el acumulado reinicia cada mes.
    // NO: continúa entre meses.
    // POR_CONFIRMAR: deja pendiente el día 1.
    ReinicioMensual = "POR_CONFIRMAR",

    Origen = HistorialEquipo,

    Tipos = Table.TransformColumnTypes(
        Origen,
        {
            {"FECHA", type date},
            {"EQUIPO", type text},
            {"RECAUDO", type number}
        }
    ),

    Equipos = Table.TransformColumns(
        Tipos,
        {{"EQUIPO",
            each if _ = null then null
            else Text.Upper(Text.Trim(_)),
            type nullable text}}
    ),

    Datos = Table.SelectRows(
        Equipos,
        each [FECHA] <> null
            and [EQUIPO] <> null
            and [EQUIPO] <> ""
    ),

    Conteos = Table.Group(
        Datos,
        {"EQUIPO", "FECHA"},
        {{"Cantidad", each Table.RowCount(_), Int64.Type}}
    ),

    Unicos =
        if Table.RowCount(
            Table.SelectRows(Conteos, each [Cantidad] > 1)
        ) > 0
        then error "Hay registros duplicados del mismo equipo y fecha."
        else Datos,

    FechaAnterior = Table.AddColumn(
        Unicos,
        "FECHA_ANTERIOR",
        each Date.AddDays([FECHA], -1),
        type date
    ),

    BuscarAnterior = Table.NestedJoin(
        FechaAnterior,
        {"EQUIPO", "FECHA_ANTERIOR"},
        Unicos,
        {"EQUIPO", "FECHA"},
        "Anterior",
        JoinKind.LeftOuter
    ),

    Expandir = Table.ExpandTableColumn(
        BuscarAnterior,
        "Anterior",
        {"RECAUDO"},
        {"RECUPERO_ANTERIOR"}
    ),

    BaseComparacion = Table.AddColumn(
        Expandir,
        "BASE_COMPARACION",
        each
            if Date.Day([FECHA]) = 1 then
                if ReinicioMensual = "SI" then 0
                else if ReinicioMensual = "NO"
                    then [RECUPERO_ANTERIOR]
                else null
            else [RECUPERO_ANTERIOR],
        type nullable number
    ),

    CalcularDiario = Table.AddColumn(
        BaseComparacion,
        "RECUPERO_DIARIO",
        each
            if [RECAUDO] = null
                or [BASE_COMPARACION] = null
            then null
            else [RECAUDO] - [BASE_COMPARACION],
        type nullable number
    ),

    Resultado = Table.Sort(
        CalcularDiario,
        {
            {"EQUIPO", Order.Ascending},
            {"FECHA", Order.Ascending}
        }
    )
in
    Resultado