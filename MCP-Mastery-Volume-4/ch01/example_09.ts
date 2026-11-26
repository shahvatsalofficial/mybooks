import * as duckdb from "@duckdb/node-api";

async function runDuckDbQuery(query: string, parquetFilePath: string) {
  const instance = await duckdb.DuckDBInstance.create(":memory:");
  const connection = await instance.connect();

  // Enforce memory and thread ceilings
  await connection.run("SET memory_limit = '2GB';");
  await connection.run("SET threads = 4;");
  await connection.run("SET enable_progress_bar = false;");

  // Execute query directly against Parquet file using zero-copy scanning
  const sanitizedQuery = query.replace(/\$PARQUET/g, `'${parquetFilePath}'`);
  const reader = await connection.runAndReadAll(sanitizedQuery);
  const rows = reader.getRows();

  return rows;
}
