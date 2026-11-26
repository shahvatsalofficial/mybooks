# finops_chargeback_report.py — Enterprise Monthly Cost Attribution
import pandas as pd
from typing import List, Dict, Any

class FinOpsReportGenerator:
    def __init__(self, raw_telemetry_records: List[Dict[str, Any]]):
        self.df = pd.DataFrame(raw_telemetry_records)

    def generate_department_summary(self) -> pd.DataFrame:
        """Aggregates spend by Cost Center, Project, and Model Family."""
        pivot = self.df.pivot_table(
            index=["department", "cost_center"],
            columns="model",
            values=["prompt_tokens", "completion_tokens", "estimated_cost_usd"],
            aggfunc="sum",
            fill_value=0
        )
        return pivot

    def export_excel(self, output_filename: str):
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            # Sheet 1: Executive Summary
            exec_summary = self.df.groupby("department")["estimated_cost_usd"].sum().reset_index()
            exec_summary.to_excel(writer, sheet_name="Executive_Summary", index=False)

            # Sheet 2: Model Breakdown
            model_summary = self.df.groupby(["department", "model"])["estimated_cost_usd"].sum().unstack().fillna(0)
            model_summary.to_excel(writer, sheet_name="Model_Breakdown")

            # Sheet 3: Granular Log
            self.df.to_excel(writer, sheet_name="Raw_Transactions", index=False)

        print(f"FinOps Excel Chargeback Ledger generated: {output_filename}")
