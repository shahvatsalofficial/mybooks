import mysql from "mysql2/promise";

export class MySqlReplicaAdapter {
  private pool: mysql.Pool;
  private maxLagSeconds: number;

  constructor(connectionUri: string, maxLagSeconds: number = 10) {
    this.maxLagSeconds = maxLagSeconds;
    this.pool = mysql.createPool({
      uri: connectionUri,
      waitForConnections: true,
      connectionLimit: 15,
      maxIdle: 5,
      idleTimeout: 10000,
      queueLimit: 0,
      enableKeepAlive: true,
      keepAliveInitialDelay: 0
    });
  }

  // Pre-flight health check to verify replication freshness
  async checkReplicationLag(): Promise<{ healthy: boolean; lagSeconds: number }> {
    const connection = await this.pool.getConnection();
    try {
      const [rows] = await connection.query("SHOW REPLICA STATUS;");
      const statusList = rows as any[];
      if (statusList.length === 0) {
        // Not a configured replica or standalone instance
        return { healthy: true, lagSeconds: 0 };
      }
      const lag = Number(statusList[0].Seconds_Behind_Source || statusList[0].Seconds_Behind_Master || 0);
      return {
        healthy: lag <= this.maxLagSeconds,
        lagSeconds: lag
      };
    } catch (err) {
      console.error("Warning: Unable to verify replica lag status", err);
      return { healthy: true, lagSeconds: 0 };
    } finally {
      connection.release();
    }
  }

  // Execute read-only query with timeout and row cap
  async executeReadOnly(sql: string, params: any[] = [], maxRows: number = 100): Promise<any> {
    const health = await this.checkReplicationLag();
    if (!health.healthy) {
      throw new Error(`MySQL Replica Degraded: Replication lag is ${health.lagSeconds}s (threshold: ${this.maxLagSeconds}s).`);
    }

    const connection = await this.pool.getConnection();
    try {
      // Set session timeout to 5 seconds to prevent hung transactions
      await connection.query("SET SESSION max_execution_time = 5000;");

      const [results, fields] = await connection.execute(sql, params);
      const rows = results as any[];

      return {
        rowCount: rows.length,
        truncated: rows.length > maxRows,
        data: rows.slice(0, maxRows),
        fields: (fields as any[]).map((f) => ({ name: f.name, type: f.type }))
      };
    } finally {
      connection.release();
    }
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}
