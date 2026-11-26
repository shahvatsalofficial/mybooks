// Anti-Pattern: Unbounded optional sprawl
interface BadDbInput {
  action: "create" | "migrate" | "drop";
  tableName?: string;
  migrationScript?: string;
  forceDrop?: boolean;
}
