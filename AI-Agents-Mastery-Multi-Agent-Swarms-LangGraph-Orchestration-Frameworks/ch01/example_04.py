if __name__ == "__main__":
    supervisor = SwarmSupervisor()
    result = supervisor.run_objective("Implement production OAuth2 PKCE challenge pair generator.")
    print("\n--- FINAL SWARM SUMMARY ---")
    print(f"Outcome: {result['status']}")
    print(f"Total Inter-Agent Messages: {result['total_messages']}")
    print(f"Code Output:\n{result['final_code']}")
