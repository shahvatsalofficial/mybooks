from langgraph.constants import Send

class SectionInput(BaseModel):
    section_id: int
    title: str
    content: str

class SectionProcessingState(TypedDict):
    document_title: str
    sections: List[SectionInput]
    processed_summaries: Annotated[List[str], operator.add]

def section_processor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Worker node processing a single dynamic partition."""
    sec_id = state["section_id"]
    title = state["title"]
    print(f"[WORKER] Processing section {sec_id}: '{title}'")
    summary = f"Summary of Sec {sec_id} ({title}): Verified compliant."
    return {"processed_summaries": [summary]}

def dynamic_fanout_router(state: SectionProcessingState) -> List[Send]:
    """Evaluates state and returns dynamic Send dispatches."""
    send_commands = []
    for sec in state["sections"]:
        payload = {"section_id": sec.section_id, "title": sec.title, "content": sec.content}
        send_commands.append(Send("section_processor_node", payload))
        
    print(f"[FAN-OUT] Emitting {len(send_commands)} parallel Send tasks...")
    return send_commands
