if __name__ == "__main__":
    task_prompt = (
        "Write a Python script that calculates the SHA-256 hash of the string 'Antigravity_Swarm_2026' "
        "and prints the final hash in uppercase to stdout."
    )
    
    print("\n--- INITIATING AUTOGEN TWO-AGENT CHAT LOOP ---")
    user_proxy.initiate_chat(
        coder_agent,
        message=task_prompt
    )
