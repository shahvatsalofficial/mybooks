server.tool(
  "export_notes_to_json",
  {
    tag: z.string().optional().describe("Filter notes by category tag")
  },
  async ({ tag }) => {
    let sql = "SELECT slug, title, content, tags, updated_at FROM notes";
    const params: string[] = [];

    if (tag) {
      sql += " WHERE tags LIKE ?";
      params.push(`%${tag.toLowerCase()}%`);
    }

    const rows = db.prepare(sql).all(...params);
    const jsonOutput = JSON.stringify(rows, null, 2);

    return {
      content: [
        {
          type: "text",
          text: jsonOutput
        }
      ]
    };
  }
);
