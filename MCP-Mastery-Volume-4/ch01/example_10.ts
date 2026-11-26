import oracledb from "oracledb";

async function queryOracleLedger(sql: string, params: Record<string, any>) {
  const connection = await oracledb.getConnection({
    user: process.env.ORACLE_USER,
    password: process.env.ORACLE_PASSWORD,
    connectString: process.env.ORACLE_CONNECT_STRING // e.g. "oracle.corp:1521/FINANCE"
  });

  try {
    const result = await connection.execute(sql, params, {
      outFormat: oracledb.OUT_FORMAT_OBJECT,
      maxRows: 100,
      timeout: 10 // 10 seconds execution timeout
    });
    return result.rows;
  } finally {
    await connection.close(); // Return connection to pool
  }
}
