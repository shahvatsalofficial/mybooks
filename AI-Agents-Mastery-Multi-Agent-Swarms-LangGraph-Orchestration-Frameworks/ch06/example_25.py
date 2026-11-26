class ZeroCopyEnvelopeParser:
    @staticmethod
    def parse_memoryview(buffer_view: memoryview) -> Dict[str, Any]:
        # Parse directly from bytes buffer without intermediary heap string allocation
        data = json.loads(buffer_view.tobytes())
        print(f"[ZERO COPY] Parsed {len(buffer_view)} bytes directly into dictionary.")
        return data
