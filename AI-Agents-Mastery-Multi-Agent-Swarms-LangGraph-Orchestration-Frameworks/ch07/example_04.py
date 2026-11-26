if __name__ == "__main__":
    store = ConcurrentSharedStore()
    state_id = "claim_session_9921"
    store.write_initial(state_id, {"status": "INITIAL_REVIEW", "credit_score": 710}, "SystemInit")
    
    print("\n--- INITIATING CONCURRENT WRITE TEST ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(simulate_agent_worker, store, state_id, "RiskAgent_01", "status", "REJECT_RISK")
        f2 = executor.submit(simulate_agent_worker, store, state_id, "FraudAgent_02", "status", "FLAG_FRAUD")
        
        print(f1.result())
        print(f2.result())
        
    final = store.get(state_id)
    print("\n--- FINAL STORE STATE ---")
    print(f"Final Version: {final.version}")
    print(f"Committed By: {final.last_updated_by}")
    print(f"Final Data: {final.data}")
