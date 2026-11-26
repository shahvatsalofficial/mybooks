if __name__ == "__main__":
    print("\n--- INITIATING CREWAI WORKFLOW EXECUTION ---")
    result = publishing_crew.kickoff()
    
    print("\n--- FINAL PUBLISHED ADVISORY ---")
    print(result)
    print("\n--- USAGE TELEMETRY ---")
    print(f"Total Tokens Consumed: {publishing_crew.usage_metrics.total_tokens}")
    print(f"Successful Requests: {publishing_crew.usage_metrics.successful_requests}")
