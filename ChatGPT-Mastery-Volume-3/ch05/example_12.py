# semantic_cache_invalidator.py
import redis
import json
import time

class SemanticCacheInvalidationEngine:
    def __init__(self, redis_client: redis.Redis, stream_name: str = "doc_updates_stream"):
        self.r = redis_client
        self.stream_name = stream_name
        self.group_name = "cache_invalidation_workers"
        self._init_consumer_group()

    def _init_consumer_group(self):
        try:
            self.r.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError:
            pass # Group already exists

    def process_invalidation_events(self):
        print(f"Listening for document invalidation events on stream: {self.stream_name}")
        while True:
            events = self.r.xreadgroup(self.group_name, "worker-1", {self.stream_name: ">"}, count=10, block=2000)
            if not events:
                continue
                
            for stream, messages in events:
                for message_id, payload in messages:
                    doc_id = payload.get(b"document_id", b"").decode("utf-8")
                    version = payload.get(b"version", b"").decode("utf-8")
                    
                    # Search semantic cache for all keys citing this document_id
                    affected_cache_keys = self.r.smembers(f"doc_citations:{doc_id}")
                    if affected_cache_keys:
                        pipe = self.r.pipeline()
                        for key in affected_cache_keys:
                            pipe.delete(key)
                        pipe.delete(f"doc_citations:{doc_id}")
                        pipe.execute()
                        print(f"Purged {len(affected_cache_keys)} stale cache entries for document: {doc_id} v{version}")
                        
                    self.r.xack(self.stream_name, self.group_name, message_id)

    def emit_doc_update(self, doc_id: str, new_version: str):
        self.r.xadd(self.stream_name, {"document_id": doc_id, "version": new_version, "timestamp": str(time.time())})
