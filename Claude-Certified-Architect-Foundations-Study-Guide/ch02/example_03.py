from dataclasses import dataclass, asdict


@dataclass
class PendingApproval:
    ticket_id: str
    messages: list[dict]
    pending_tool_id: str
    tool_name: str
    tool_input: dict


def serialize_checkpoint(cp: PendingApproval) -> str:
    return json.dumps(asdict(cp), default=str)


def build_resume_messages(cp: PendingApproval, approved: bool) -> list[dict]:
    result_text = (
        f"Executed {cp.tool_name} successfully."
        if approved
        else "Action rejected by human operator."
    )
    updated = list(cp.messages)
    updated.append({
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": cp.pending_tool_id,
            "is_error": not approved,
            "content": result_text,
        }],
    })
    return updated
