from crewai.tools import BaseTool

class SQLQueryInput(BaseModel):
    query_string: str = Field(description="The sanitized SQL SELECT query to execute")
    max_records: int = Field(default=10, ge=1, le=100, description="Maximum row limit")

class EnterpriseDatabaseTool(BaseTool):
    name: str = "enterprise_database_query_tool"
    description: str = (
        "Executes read-only SQL queries against the corporate transaction database. "
        "Input must be a valid SQL SELECT statement. Updates and deletes are rejected."
    )
    args_schema: type[BaseModel] = SQLQueryInput

    def _run(self, query_string: str, max_records: int = 10) -> str:
        clean_query = query_string.strip().upper()
        # Security perimeter check
        if any(keyword in clean_query for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]):
            return "SECURITY REJECTION: Only read-only SELECT operations are permitted."
        
        # Mock database response
        print(f"[TOOL: DB] Executing query: '{query_string}' (Limit: {max_records})")
        return (
            f"Query Results (Limited to {max_records} rows):\n"
            "| transaction_id | account_id | amount_usd | status |\n"
            "| TX-9912        | ACC-4401   | 4,500.00   | SETTLED |\n"
            "| TX-9913        | ACC-2219   | 12,850.00  | PENDING |"
        )
