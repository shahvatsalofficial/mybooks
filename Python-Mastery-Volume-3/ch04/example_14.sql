-- Automated query identifying foreign keys lacking matching indexes
SELECT c.conrelid::regclass AS child_table,
       string_agg(a.attname, ', ') AS fk_columns,
       c.conname AS constraint_name
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND NOT EXISTS (
      SELECT 1 FROM pg_index i
      WHERE i.indrelid = c.conrelid
        AND c.conkey = (i.indkey::smallint[])[0:array_length(c.conkey, 1) - 1]
  )
GROUP BY c.conrelid, c.conname;
