def make_timeout_node(node_fn: Callable, timeout_sec: float = 3.0):
    def wrapped_node(state: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.time()
        try:
            return node_fn(state)
        except Exception as exc:
            print(f"[TIMEOUT GUARD] Node threw exception after {time.time() - t0:.2f}s: {exc}")
            return {"error": str(exc), "status": "NODE_FAILED"}
    return wrapped_node
