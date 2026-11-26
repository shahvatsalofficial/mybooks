import { z } from "zod";

export const DatabaseQuerySchema = z.object({
  // Enforce table name conforms to SQL identifier rules (no spaces, no semicolons)
  tableName: z.string()
    .min(1, "Table name cannot be empty")
    .max(64, "Table name cannot exceed 64 characters")
    .regex(/^[a-zA-Z_][a-zA-Z0-9_]*$/, "Invalid SQL table identifier syntax"),

  // Bounded integer with automatic string-to-number coercion
  limit: z.coerce.number()
    .int("Limit must be an integer")
    .min(1, "Limit must be at least 1")
    .max(100, "Maximum allowed limit is 100 rows to preserve context window")
    .default(25),

  // Array of column names with strict uniqueness and element validation
  columns: z.array(
    z.string().regex(/^[a-zA-Z_][a-zA-Z0-9_]*$/, "Invalid column name")
  ).min(1, "Must request at least one column").default(["id"]),

  // Optional filter object with strict allowed comparison operators
  filters: z.array(
    z.object({
      field: z.string().regex(/^[a-zA-Z_][a-zA-Z0-9_]*$/),
      operator: z.enum(["EQ", "NEQ", "GT", "LT", "LIKE", "IN"]),
      value: z.union([z.string(), z.number(), z.boolean(), z.array(z.string())])
    })
  ).optional().default([])
});

export type DatabaseQueryInput = z.infer<typeof DatabaseQuerySchema>;
