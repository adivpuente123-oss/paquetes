let
    Origen = BaseRecupero,
    ConFecha = Table.SelectRows(Origen, each [FECHA_CORTE] <> null),
    UltimoCorte = if Table.IsEmpty(ConFecha) then null else List.Max(ConFecha[FECHA_CORTE]),
    // Antes de iniciar el historial conserva la tabla original. Despues usa un solo cierre completo.
    Actual = if UltimoCorte = null then Origen else Table.SelectRows(ConFecha, each [FECHA_CORTE] = UltimoCorte),
    Conteos = if UltimoCorte = null then #table({"DNI", "Filas"}, {}) else Table.Group(Actual, {"DNI"}, {{"Filas", each Table.RowCount(_), Int64.Type}}),
    Duplicados = Table.SelectRows(Conteos, each [Filas] > 1),
    Validado = if Table.RowCount(Duplicados) > 0 then error "Hay DNI duplicados en el ultimo cierre. No se suman para evitar inflar el recupero." else Actual,
    SinAuxiliar = Table.RemoveColumns(Validado, {"ACUMULADO_NUM"})
in
    SinAuxiliar
