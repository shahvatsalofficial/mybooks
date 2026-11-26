# Inspecting Code Interpreter Execution Artifacts from a Completed Run Step
run_steps = await client.beta.threads.runs.steps.list(
    thread_id=thread.id,
    run_id=run.id
)

for step in run_steps.data:
    if step.step_details.type == "tool_calls":
        for tool_call in step.step_details.tool_calls:
            if tool_call.type == "code_interpreter":
                code_input = tool_call.code_interpreter.input
                print(f"
--- Python Code Executed by Model ---
{code_input}")
                for output in tool_call.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"Stdout:
{output.logs}")
                    elif output.type == "image":
                        image_file_id = output.image.file_id
                        print(f"Generated Visualization Artifact: {image_file_id}")
