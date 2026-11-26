{
  name: "pg_explain_plan",
  description: "Runs EXPLAIN (ANALYZE, FORMAT JSON) on a read-only query to inspect execution plan cost.",
  inputSchema: {
    type: "object",
    properties: {
      sql: { type: "string", description: "The SQL statement to explain." }
    },
    required: ["sql"]
  }
}
// Execution handler:
const res = await client.query(`EXPLAIN (ANALYZE, COSTS, FORMAT JSON) ${sanitizedSql}`);
const planNode = res.rows[0]["QUERY PLAN"][0]["Plan"];
const summary = {
  totalCost: planNode["Total Cost"],
  actualTimeMs: planNode["Actual Total Time"],
  nodeType: planNode["Node Type"]
};
return { content: [{ type: "text", text: JSON.stringify(summary, null, 2) }] };
