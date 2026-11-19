let
    // SI: acumulado mensual. NO: acumulado que continua entre meses.
    // Hasta confirmarlo, el dia 1 se deja pendiente, evitando una resta equivocada.
    ReinicioMensual = "POR_CONFIRMAR",
    ConfigValida = if List.Contains({"SI", "NO", "POR_CONFIRMAR"}, ReinicioMensual) then ReinicioMensual else error "ReinicioMensual debe ser SI, NO o POR_CONFIRMAR.",
    ConFecha = Table.SelectRows(BaseRecupero, each [FECHA_CORTE] <> null),
    SinDni = Table.SelectRows(ConFecha, each [DNI] = null),
    IdValidos = if Table.RowCount(SinDni) > 0 then error "Hay cortes con fecha pero sin DNI: completa el identificador antes de actualizar." else ConFecha,
    Conteos = Table.Group(IdValidos, {"DNI", "FECHA_CORTE"}, {{"Filas", each Table.RowCount(_), Int64.Type}}),
    Duplicados = Table.SelectRows(Conteos, each [Filas] > 1),
    Unicos = if Table.RowCount(Duplicados) > 0 then error "Hay mas de una fila por DNI y cierre: corrige los duplicados antes de actualizar." else IdValidos,
    Periodo = Table.AddColumn(Unicos, "PERIODO_CORTE", each Date.StartOfMonth([FECHA_CORTE]), type date),
    FechaAnterior = Table.AddColumn(Periodo, "FECHA_ANTERIOR", each Date.AddDays([FECHA_CORTE], -1), type date),
    Cruce = Table.NestedJoin(FechaAnterior, {"DNI", "FECHA_ANTERIOR"}, Unicos, {"DNI", "FECHA_CORTE"}, "Anterior", JoinKind.LeftOuter),
    ValorAnterior = Table.ExpandTableColumn(Cruce, "Anterior", {"ACUMULADO_NUM"}, {"ACUMULADO_PREVIO"}),
    BaseDiferencia = Table.AddColumn(ValorAnterior, "BASE_COMPARACION", each if Date.Day([FECHA_CORTE]) = 1 then if ConfigValida = "SI" then 0 else if ConfigValida = "NO" then [ACUMULADO_PREVIO] else null else [ACUMULADO_PREVIO], type nullable number),
    Diferencia = Table.AddColumn(BaseDiferencia, "RECUPERO_DIARIO", each if [ACUMULADO_NUM] = null or [BASE_COMPARACION] = null then null else [ACUMULADO_NUM] - [BASE_COMPARACION], type nullable number),
    Control = Table.AddColumn(Diferencia, "CONTROL_DIARIO", each if [ACUMULADO_NUM] = null then "ACUMULADO NO NUMERICO" else if Date.Day([FECHA_CORTE]) = 1 and ConfigValida = "POR_CONFIRMAR" then "CONFIRMAR REINICIO MENSUAL" else if [BASE_COMPARACION] = null then "SIN CORTE ANTERIOR CONSECUTIVO" else if [RECUPERO_DIARIO] < 0 then "AJUSTE NEGATIVO: REVISAR" else "OK", type text),
    Limpieza = Table.RemoveColumns(Control, {"FECHA_ANTERIOR"}),
    Orden = Table.Sort(Limpieza, {{"FECHA_CORTE", Order.Ascending}, {"Equipo", Order.Ascending}, {"ASESOR_CRR", Order.Ascending}})
in
    Orden
