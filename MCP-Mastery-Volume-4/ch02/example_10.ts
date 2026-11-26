// Tabular Projection Formatter for Agent Context
export function formatTabularPreview(columns: string[], rows: any[][], totalRowCount: number): string {
  let md = `### Tabular Data Preview (${rows.length} of ${totalRowCount} rows displayed)\n\n`;
  
  // Format header
  md += `| ${columns.join(" | ")} |\n`;
  md += `| ${columns.map(() => "---").join(" | ")} |\n`;

  // Format sample rows
  for (const row of rows) {
    const formattedCells = row.map((val) => {
      if (val === null || val === undefined) return "*null*";
      const str = String(val);
      return str.length > 30 ? `${str.substring(0, 27)}...` : str;
    });
    md += `| ${formattedCells.join(" | ")} |\n`;
  }

  md += `\n*Note: Use pagination parameters (start_row, row_count) to inspect subsequent records.*`;
  return md;
}
