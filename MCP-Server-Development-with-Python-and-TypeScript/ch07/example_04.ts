const DateRangeSchema = z.object({
  start_date: z.string().datetime(),
  end_date: z.string().datetime()
}).refine(
  (data) => new Date(data.end_date) > new Date(data.start_date),
  {
    message: "end_date must be strictly chronologically after start_date",
    path: ["end_date"]
  }
);
