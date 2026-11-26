import neo4j from "neo4j-driver";

const driver = neo4j.driver(
  process.env.NEO4J_URI || "bolt://localhost:7687",
  neo4j.auth.basic(process.env.NEO4J_USER || "neo4j", process.env.NEO4J_PASSWORD || "")
);

async function executeCypherTraversal(cypherQuery: string, parameters: Record<string, any>) {
  const session = driver.session({ defaultAccessMode: neo4j.session.READ });
  try {
    const records = await session.readTransaction(async (tx) => {
      const res = await tx.run(cypherQuery, parameters);
      return res.records.map((r) => r.toObject());
    });
    return records;
  } finally {
    await session.close();
  }
}
