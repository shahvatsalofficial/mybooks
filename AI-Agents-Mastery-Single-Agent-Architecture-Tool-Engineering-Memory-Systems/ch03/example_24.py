# Conceptual harness using wasmtime-py
from wasmtime import Engine, Store, Module, Instance, Limits

def run_wasm_sandboxed(wasm_bytes: bytes, input_val: int) -> int:
    engine = Engine()
    # Enforce strict memory limits (max 16 pages = 1MB)
    store = Store(engine)
    store.set_limits(Limits(memory_size=16 * 64 * 1024))
    
    module = Module(engine, wasm_bytes)
    instance = Instance(store, module, [])
    run_fn = instance.exports(store)["run"]
    return run_fn(store, input_val)
