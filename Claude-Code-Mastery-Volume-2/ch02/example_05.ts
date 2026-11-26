import { z } from "zod";

export const QueryTenantLogsSchema = {
  tenantId: z.string()
    .uuid()
    .describe("The unique UUIDv4 identifier of the customer tenant organization"),
  
  severity: z.enum(["DEBUG", "INFO", "WARN", "ERROR", "FATAL"])
    .default("ERROR")
    .describe("Minimum log severity threshold to filter"),
    
  timeRangeHours: z.number()
    .int()
    .min(1)
    .max(168)
    .default(24)
    .describe("Number of historical hours to scan (1 to 168 hours / 7 days)"),
    
  includeStackTrace: z.boolean()
    .default(false)
    .describe("Whether to include raw stack trace strings in the returned log records"),
    
  regexFilter: z.string()
    .optional()
    .describe("Optional POSIX regular expression pattern to filter log message bodies")
};
