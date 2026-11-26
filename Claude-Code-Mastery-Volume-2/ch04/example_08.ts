import { z } from "zod";

const CreateTableAction = z.object({
  action: z.literal("create"),
  tableName: z.string().regex(/^[a-z0-9_]+$/),
  columns: z.array(z.object({
    name: z.string(),
    type: z.enum(["TEXT", "INTEGER", "BOOLEAN", "TIMESTAMP"]),
    nullable: z.boolean().default(false)
  })).min(1)
});

const MigrateTableAction = z.object({
  action: z.literal("migrate"),
  migrationId: z.string().regex(/^V[0-9]{3}__[a-z_]+\.sql$/),
  dryRun: z.boolean().default(true)
});

const DropTableAction = z.object({
  action: z.literal("drop"),
  tableName: z.string().regex(/^[a-z0-9_]+$/),
  confirmDestructionPhrase: z.literal("PERMANENTLY_DESTROY_DATA")
});

export const DatabaseAdminSchema = z.discriminatedUnion("action", [
  CreateTableAction,
  MigrateTableAction,
  DropTableAction
]);
