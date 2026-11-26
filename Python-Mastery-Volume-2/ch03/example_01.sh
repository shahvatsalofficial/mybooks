# Run in true multi-core free-threaded mode
   PYTHON_GIL=0 python3.13t service_entrypoint.py

   # Emergency fallback: re-enable GIL if legacy extension issues occur
   PYTHON_GIL=1 python3.13t service_entrypoint.py
   ```

2. **Command-Line Switch (`-X gil=0`)**:
   Developers can configure the GIL state per process invocation:
   ```bash
   python3.13t -X gil=0 -m pytest tests/concurrency/
   ```

3. **Programmatic Inspection & API (`sys._is_gil_enabled()`)**:
   Applications can detect the ambient GIL state programmatically:
   ```python
   import sys

   def report_concurrency_mode() -> None:
       if hasattr(sys, "_is_gil_enabled"):
           is_active = sys._is_gil_enabled()
           print(f"Runtime Mode: {'GIL Active (Serialized)' if is_active else 'Free-Threaded (Multi-Core Parallel)'}")
       else:
           print("Runtime Mode: Standard Legacy CPython (GIL Mandatory)")
   ```

Understanding these flags allows operations teams to execute blue-green deployments, testing free-threaded performance on isolated worker nodes while maintaining immediate rollback capabilities.

![Figure 03.01: GIL vs Free-Threaded CPython Topology](assets/svg/diag_ch03_gil_vs_freethreaded_topology.svg)

### The Architectural Challenges of Removing the GIL

Eliminating the GIL was not merely a matter of deleting a mutex. In standard CPython, thousands of critical internal operations relied on the ambient assumption of global single-threaded execution:
1. **Reference Counting**: Every variable assignment, function argument pass, and tuple unpacking executes `Py_INCREF` and `Py_DECREF`. In standard CPython, this is an ordinary non-atomic memory increment: `op->ob_refcnt++`. Under multi-core parallel execution, raw non-atomic increments lead to catastrophic race conditions, missed decrements, double-free faults, and heap corruption. However, replacing every refcount with atomic instructions (`std::atomic`) introduces severe hardware cache-coherence traffic (bus locking), degrading single-threaded execution by over $40\%$.
2. **Memory Allocation**: CPython's default small-object allocator (`PyObject_Malloc` / pymalloc) maintained global, thread-unsafe memory arenas.
3. **Internal Container Safety**: Dictionaries, lists, sets, and object type caches were modified in-place without internal locking, relying on the GIL for coarse-grained synchronization.

PEP 703 resolved these challenges through three foundational innovations: **Biased Reference Counting**, **Mimalloc Thread-Local Memory Arenas**, and **Immortal / Deferred Object Sweeps**.

---

## 2. Biased Reference Counting (BRC) & Object Lifecycle

To preserve single-threaded performance while guaranteeing multi-threaded safety, PEP 703 introduces **Biased Reference Counting (BRC)**.

![Figure 03.02: Biased Reference Counting Lifecycle](assets/svg/diag_ch03_biased_refcounting_lifecycle.svg)

### The Mechanics of Biased Reference Counting

In BRC, every allocated Python object is "biased" toward the specific operating system thread that created it (the owning thread). The object's header is partitioned to maintain two distinct reference counts:

1. **Local Refcount (`ob_ref_local`)**: Modified *exclusively* by the owning thread. Because only the owning thread ever reads or writes this field, modifications are performed via ordinary, non-atomic CPU instructions (`ADD` / `SUB`), completely avoiding expensive inter-core cache-bus synchronization.
2. **Shared Refcount (`ob_ref_shared`)**: Modified by any foreign thread that references the object. Because multiple foreign threads can access the object simultaneously, modifications to this field use atomic Compare-And-Swap (`lock cmpxchg` / `atomic_fetch_add`) instructions.

### The 64-Bit Object Header Bit Layout Under PEP 703

Under standard CPython, the base header `PyObject` contains two 64-bit words: `ob_refcnt` (an unsigned 64-bit integer) and `ob_type` (a pointer to the `PyTypeObject`). 

Under PEP 703, `PyObject` reorganizes this header into a compact, multi-field 64-bit word that packs both reference counters and runtime thread state:
