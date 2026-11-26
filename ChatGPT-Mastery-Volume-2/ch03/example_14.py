"""
Hands-On Lab: Autonomous Monte Carlo Portfolio Risk Auditor
Demonstrates end-to-end Assistants v2: File uploads, sandboxed Code Interpreter,
visualization artifact downloads, and real-time streaming tokens.
Author: Vatsal Shah, Enterprise AI Architect
"""
import os
import io
import sys
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

CSV_POSITION_DATA = """ticker,asset_class,shares,cost_basis,current_price,volatility_annual
NVDA,EQUITY,500,450.00,128.50,0.48
MSFT,EQUITY,300,320.00,445.00,0.22
AAPL,EQUITY,400,165.00,225.00,0.20
GOOGL,EQUITY,250,130.00,180.00,0.26
TLT,FIXED_INCOME,1200,98.00,92.50,0.14
HYG,FIXED_INCOME,800,74.00,77.20,0.08
GLD,COMMODITY,600,180.00,235.00,0.15
"""

async def run_monte_carlo_lab():
    print("
=======================================================")
    print("🚀 INITIATING AUTONOMOUS MONTE CARLO RISK AUDIT LAB")
    print("=======================================================
")

    # Step 1: Upload CSV position dataset to OpenAI Files
    csv_bytes = io.BytesIO(CSV_POSITION_DATA.encode("utf-8"))
    csv_bytes.name = "portfolio_positions.csv"
    
    print("1. Uploading position dataset to OpenAI Files API...")
    uploaded_file = await client.files.create(
        file=csv_bytes,
        purpose="assistants"
    )
    print(f"   ✅ File uploaded successfully. File ID: {uploaded_file.id}")

    # Step 2: Provision Assistant with Code Interpreter
    print("
2. Provisioning Quantitative Risk Assistant...")
    assistant = await client.beta.assistants.create(
        name="Quantitative Risk Simulation Specialist",
        instructions=(
            "You are a Senior Quantitative Portfolio Risk Architect. "
            "You analyze asset allocations by reading uploaded CSV files, running statistical models "
            "in Python, executing 10,000-iteration Monte Carlo simulations, and generating "
            "publication-grade visualization charts. Always display calculated 95% and 99% 1-day Value at Risk (VaR)."
        ),
        model="gpt-4o",
        tools=[{"type": "code_interpreter"}],
        tool_resources={
            "code_interpreter": {
                "file_ids": [uploaded_file.id]
            }
        }
    )
    print(f"   ✅ Assistant provisioned. ID: {assistant.id}")

    # Step 3: Create Persistent Thread
    thread = await client.beta.threads.create()
    print(f"   ✅ Persistent Thread created. ID: {thread.id}")

    # Step 4: Submit Analysis Prompt
    analysis_prompt = (
        "Read '/mnt/data/portfolio_positions.csv'. Calculate the current total portfolio value. "
        "Run a 10,000-iteration Monte Carlo simulation simulating 30-day forward portfolio value changes, "
        "assuming a multivariate normal distribution of returns. "
        "Plot a histogram of simulated final portfolio values with 95% and 99% VaR marked as vertical lines. "
        "Save the plot to 'monte_carlo_var_distribution.png'."
    )
    
    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=analysis_prompt
    )

    # Step 5: Execute Streaming Run
    print("
3. Launching Real-Time Streaming Run...")
    print("-------------------------------------------------------")
    
    async with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        max_prompt_tokens=15000,
        max_completion_tokens=3000
    ) as stream:
        async for event in stream:
            if event.event == "thread.message.delta":
                delta_content = event.data.delta.content
                if delta_content and len(delta_content) > 0:
                    text_chunk = delta_content[0].text.value
                    sys.stdout.write(text_chunk)
                    sys.stdout.flush()
                    
            elif event.event == "thread.run.step.created":
                step_details = event.data.step_details
                if step_details.type == "tool_calls":
                    print("

[⚙️ Code Interpreter Executing Python Simulation...]")

    print("
-------------------------------------------------------")
    print("✅ Streaming Turn Completed!")

    # Step 6: Inspect generated image artifacts and download
    print("
4. Inspecting Generated Artifacts from Code Interpreter...")
    steps = await client.beta.threads.runs.steps.list(
        thread_id=thread.id,
        run_id=stream.current_run.id
    )
    
    generated_image_file_id = None
    for step in steps.data:
        if step.step_details.type == "tool_calls":
            for tc in step.step_details.tool_calls:
                if tc.type == "code_interpreter":
                    for output in tc.code_interpreter.outputs:
                        if output.type == "image":
                            generated_image_file_id = output.image.file_id
                            print(f"   🖼️ Found Generated Visualization Artifact: {generated_image_file_id}")

    if generated_image_file_id:
        print(f"   📥 Downloading {generated_image_file_id} from OpenAI...")
        image_content = await client.files.content(generated_image_file_id)
        with open("scratch/downloaded_monte_carlo_chart.png", "wb") as f:
            f.write(image_content.read())
        print("   ✅ Chart saved locally to 'scratch/downloaded_monte_carlo_chart.png'!")

    # Step 7: Clean up ephemeral cloud entities
    print("
5. Cleaning up ephemeral lab resources...")
    await client.files.delete(uploaded_file.id)
    await client.beta.assistants.delete(assistant.id)
    await client.beta.threads.delete(thread.id)
    print("   ✅ Ephemeral File, Assistant, and Thread deleted successfully.")
    print("
🎯 LAB EXECUTION COMPLETED WITH 100% OPERATIONAL SUCCESS!")

if __name__ == "__main__":
    asyncio.run(run_monte_carlo_lab())
