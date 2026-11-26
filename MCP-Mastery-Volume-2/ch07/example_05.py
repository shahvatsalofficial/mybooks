import os

def resolve_safe_path(base_dir: str, untrusted_path: str) -> str:
    # 1. Resolve canonical base directory (dereferencing all symlinks)
    canonical_base = os.path.realpath(os.path.abspath(base_dir))
    
    # 2. Join and resolve the target path to its absolute physical location
    target_path = os.path.abspath(os.path.join(canonical_base, untrusted_path))
    canonical_target = os.path.realpath(target_path)
    
    # 3. Cryptographically strict boundary verification using os.path.commonpath
    # commonpath guarantees that canonical_base is an ancestor directory of canonical_target
    if os.path.commonpath([canonical_base, canonical_target]) != canonical_base:
        raise PermissionError(
            f"Security Violation: Target path '{untrusted_path}' resolves "
            f"outside designated sandbox root '{base_dir}'."
        )
        
    return canonical_target
