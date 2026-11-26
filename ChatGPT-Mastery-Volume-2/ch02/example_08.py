"""
Enterprise Financial Dispatcher & Structured Output Engine
Author: Vatsal Shah, Enterprise AI Architect
Version: 2.0 (Production Hardened)
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FinancialDispatcher")

# =====================================================================
# 1. Pydantic Domain Contracts (Tool Arguments & Final Output)
# =====================================================================

class QueryMarketDataArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str = Field(description="Stock ticker symbol, e.g., MSFT, GOOGL")
    lookback_days: int = Field(default=30, ge=1, le=365, description="Historical trading days to query")

class CalculateVolatilityArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str = Field(description="Stock ticker symbol")
    annualized: bool = Field(default=True, description="Whether to compute annualized variance")

class FinancialRiskReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    executive_summary: str = Field(description="Concise C-suite summary of portfolio risk posture")
    assessed_tickers: List[str] = Field(description="List of all tickers evaluated in this audit")
    portfolio_volatility_pct: float = Field(description="Computed aggregate portfolio volatility percentage")
    hedging_recommendation: str = Field(description="Strategic options or futures hedging advisory")
    action_required: bool = Field(description="Flag indicating immediate portfolio manager intervention")

# =====================================================================
# 2. Mock Enterprise Microservice Handlers
# =====================================================================

async def mock_query_market_data(ticker: str, lookback_days: int) -> Dict[str, Any]:
    await asyncio.sleep(0.15) # Simulate async database latency
    ticker_clean = ticker.upper()
    if ticker_clean == "FAIL":
        raise ConnectionResetError("Database connection dropped on cluster read replica.")
    return {
        "ticker": ticker_clean,
        "current_price": 420.50 if ticker_clean == "MSFT" else 185.20,
        "volume_avg": 24500000,
        "history_days_returned": lookback_days
    }

async def mock_calculate_volatility(ticker: str, annualized: bool) -> Dict[str, Any]:
    await asyncio.sleep(0.12)
    vol = 0.245 if ticker.upper() == "MSFT" else 0.312
    return {
        "ticker": ticker.upper(),
        "volatility": vol * (1.0 if not annualized else 1.25),
        "confidence_interval": 0.99
    }

TOOL_REGISTRY = {
    "query_market_data": mock_query_market_data,
    "calculate_volatility": mock_calculate_volatility
}

# =====================================================================
# 3. Enterprise Dispatcher Engine
# =====================================================================

class EnterpriseFinancialDispatcher:
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            max_retries=2
        )
        self.tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "query_market_data",
                    "description": "Fetch historical market pricing and trading volume for an equity ticker.",
                    "parameters": QueryMarketDataArgs.model_json_schema(),
                    "strict": True
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_volatility",
                    "description": "Calculate statistical price variance and annualized volatility for a given ticker.",
                    "parameters": CalculateVolatilityArgs.model_json_schema(),
                    "strict": True
                }
            }
        ]

    async def _execute_single_tool(self, tool_call) -> Dict[str, Any]:
        tool_name = tool_call.function.name
        raw_args = tool_call.function.arguments
        call_id = tool_call.id

        logger.info(f"Executing tool: {tool_name} with call_id: {call_id}")
        handler = TOOL_REGISTRY.get(tool_name)
        
        if not handler:
            return {
                "tool_call_id": call_id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps({"error": f"Tool '{tool_name}' not registered in dispatcher."})
            }

        try:
            parsed_args = json.loads(raw_args)
            result = await handler(**parsed_args)
            return {
                "tool_call_id": call_id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result)
            }
        except Exception as exc:
            logger.error(f"Execution error on {tool_name}: {str(exc)}")
            return {
                "tool_call_id": call_id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps({"status": "FAILED", "reason": str(exc)})
            }

    async def run_portfolio_analysis(self, user_query: str) -> FinancialRiskReport:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Lead Quantitative Risk Architect for an institutional hedge fund. "
                    "Analyze market conditions by executing available tools, then output your final "
                    "assessment strictly conforming to the FinancialRiskReport schema."
                )
            },
            {"role": "user", "content": user_query}
        ]

        # Step 1: Initial tool selection turn
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self.tools_schema,
            tool_choice="auto",
            parallel_tool_calls=True
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        # Step 2: Handle parallel tool calls if requested
        if response_message.tool_calls:
            logger.info(f"Model dispatched {len(response_message.tool_calls)} parallel tool calls.")
            
            # Fan-out concurrent execution via asyncio.gather
            tool_tasks = [
                self._execute_single_tool(tc) 
                for tc in response_message.tool_calls
            ]
            tool_results = await asyncio.gather(*tool_tasks)

            # Re-inject tool outputs into conversation history
            for tool_output in tool_results:
                messages.append(tool_output)

        # Step 3: Final synthesis enforcing Strict Structured Output Schema
        logger.info("Requesting final structured risk report via Pydantic parse...")
        final_completion = await self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            response_format=FinancialRiskReport
        )

        report: FinancialRiskReport = final_completion.choices[0].message.parsed
        return report

# =====================================================================
# 4. Entrypoint Verification
# =====================================================================

async def main():
    dispatcher = EnterpriseFinancialDispatcher()
    query = (
        "Evaluate portfolio risk across MSFT and GOOGL. "
        "Fetch their 30-day market data and calculate annualized volatility."
    )
    print("
--- Dispatching Multi-Tool Enterprise Query ---")
    report = await dispatcher.run_portfolio_analysis(query)
    print("
✅ Verified Pydantic Risk Report Output:")
    print(json.dumps(report.model_dump(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
