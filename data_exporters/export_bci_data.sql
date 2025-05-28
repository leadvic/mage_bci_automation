INSERT INTO ps5gfk9xc0nc0s1.transacciones (fecha, codigo, ciudad, descripcion, tipo_tarjeta, monto)
SELECT *
FROM
    {{ df_1 }} AS source
WHERE
    NOT EXISTS (
        SELECT 1
        FROM ps5gfk9xc0nc0s1.transacciones AS target
        WHERE
            target.fecha IS NOT DISTINCT FROM source.fecha
            AND target.codigo IS NOT DISTINCT FROM source.codigo
            AND target.ciudad IS NOT DISTINCT FROM source.ciudad
            AND target.descripcion IS NOT DISTINCT FROM source.descripcion
            AND target.tipo_tarjeta IS NOT DISTINCT FROM source.tipo_tarjeta
            AND target.monto IS NOT DISTINCT FROM source.monto
    );