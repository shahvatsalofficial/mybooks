if __name__ == "__main__":
    test_ticket: GlobalParentState = {
        "ticket_id": "TCK-8821",
        "customer_tier": "enterprise",
        "messages": ["Customer request: Unauthorized charge on invoice INV-2026-9912. Requesting refund."],
        "active_route": "",
        "resolution_status": "pending",
        "final_resolution_summary": None
    }
    
    print("\n--- INITIATING COMPOSITE SWARM EXECUTION ---")
    final_output = parent_app.invoke(test_ticket)
    
    print("\n--- COMPOSITE SWARM OUTCOME ---")
    print(f"Ticket ID: {final_output['ticket_id']}")
    print(f"Status: {final_output['resolution_status']}")
    print(f"Resolution Summary: {final_output['final_resolution_summary']}")
    print("Conversation Log:")
    for m in final_output['messages']:
        print(f"  * {m}")
