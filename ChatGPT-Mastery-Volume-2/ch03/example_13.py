"""
Enterprise Thread Compaction & Archival Engine
Extracts historical conversational dockets, summarizes context, and rolls over cleanly.
"""
from typing import List
from openai import AsyncOpenAI
import logging

logger = logging.getLogger("ThreadCompactor")

class ThreadCompactionService:
    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def compact_and_rollover_thread(self, old_thread_id: str, assistant_id: str) -> str:
        # Step 1: Ingest all historical messages using cursor pagination
        all_messages: List[str] = []
        has_more = True
        last_id = None

        while has_more:
            kwargs = {"limit": 50, "order": "desc"}
            if last_id:
                kwargs["after"] = last_id
            page = await self.client.beta.threads.messages.list(old_thread_id, **kwargs)
            
            for msg in page.data:
                role = msg.role.upper()
                text = msg.content[0].text.value if msg.content else ""
                all_messages.append(f"{role}: {text}")

            has_more = page.has_more
            if page.data:
                last_id = page.data[-1].id

        # Reverse to chronological order
        chronological_transcript = "\n".join(reversed(all_messages))
        logger.info(f"Ingested {len(all_messages)} messages from thread {old_thread_id} for compaction.")

        # Step 2: Generate Structured Summary via Chat Completions
        summary_prompt = (
            "You are a Principal Enterprise Systems Archivist. Summarize the following "
            "conversational transcript into an executive architectural docket. "
            "Preserve all specific entity IDs, agreed financial/technical parameters, "
            "completed actions, and pending items. Be concise but exhaustive on facts:\n\n"
            f"{chronological_transcript[:60000]}"
        )

        compaction_res = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.1
        )
        executive_summary = compaction_res.choices[0].message.content

        # Step 3: Create fresh target Thread and seed Turn 0
        new_thread = await self.client.beta.threads.create()
        await self.client.beta.threads.messages.create(
            thread_id=new_thread.id,
            role="user",
            content=f"[SYSTEM MEMORY COMPACTED DOCKET FROM PREVIOUS SESSION:\n{executive_summary}\n\nPlease acknowledge and resume operations.]"
        )

        # Run one quick priming turn on the new thread
        await self.client.beta.threads.runs.create_and_poll(
            thread_id=new_thread.id,
            assistant_id=assistant_id,
            max_prompt_tokens=4000
        )

        # Step 4: Purge obsolete legacy thread
        await self.client.beta.threads.delete(old_thread_id)
        logger.info(f"Successfully compacted thread {old_thread_id} into {new_thread.id} and purged legacy entity.")
        
        return new_thread.id
