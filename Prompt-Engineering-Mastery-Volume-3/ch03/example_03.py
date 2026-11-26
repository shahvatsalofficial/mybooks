"""
Scratchpad Pruning Engine: Compresses historical ReAct turns to prevent attention decay
and maintain prompt budget within optimal token ceilings.
"""

from typing import List, Dict, Any


class ScratchpadCompactor:
    """Manages context window efficiency for long-horizon ReAct execution."""

    def __init__(self, full_fidelity_window: int = 3, max_observation_chars: int = 600):
        self.full_fidelity_window = full_fidelity_window
        self.max_observation_chars = max_observation_chars

    def truncate_observation(self, raw_obs: str) -> str:
        """Truncates voluminous payloads while preserving structural metadata."""
        if len(raw_obs) <= self.max_observation_chars:
            return raw_obs

        head_chars = int(self.max_observation_chars * 0.7)
        tail_chars = int(self.max_observation_chars * 0.3)
        omitted = len(raw_obs) - (head_chars + tail_chars)

        return (
            f"{raw_obs[:head_chars]}\n"
            f"... [SYSTEM: {omitted} characters truncated to protect token budget] ...\n"
            f"{raw_obs[-tail_chars:]}"
        )

    def render_compacted_history(self, turns: List[ReActTurn]) -> str:
        """
        Renders historical turns into a compressed XML transcript.
        Older turns are reduced to executive summaries; recent turns retain full fidelity.
        """
        if not turns:
            return ""

        rendered_blocks = []
        cutoff_index = max(0, len(turns) - self.full_fidelity_window)

        for i, turn in enumerate(turns):
            if i < cutoff_index:
                # Compressed Milestone Representation
                rendered_blocks.append(
                    f'<historical_step index="{turn.index}" tool="{turn.action_name}">\n'
                    f'  <summary>Action executed. Key outcome preserved.</summary>\n'
                    f'  <observation_digest>{self.truncate_observation(turn.observation or "")}</observation_digest>\n'
                    f'</historical_step>'
                )
            else:
                # Full Fidelity Active Window
                rendered_blocks.append(
                    f'<react_turn index="{turn.index}">\n'
                    f'  <thought>{turn.thought}</thought>\n'
                    f'  <action name="{turn.action_name}">\n'
                    f'    {json.dumps(turn.action_params, indent=2)}\n'
                    f'  </action>\n'
                    f'  {turn.observation}\n'
                    f'</react_turn>'
                )

        return "\n\n".join(rendered_blocks)
