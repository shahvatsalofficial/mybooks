from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class SafePathValidator(BaseModel):
    relative_path: str = Field(description="Relative path within the isolated workspace root")
    max_bytes: int = Field(default=64000, le=1048576, description="Maximum bytes to read into context")

class SandboxedFileSystem:
    def __init__(self, root_dir: str):
        self.root = Path(root_dir).resolve()
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        target = (self.root / relative_path).resolve()
        # Security assertion: Target must remain strictly inside root
        if not str(target).startswith(str(self.root)):
            raise PermissionError(
                f"Path Traversal Violation: Path '{relative_path}' resolves outside allowed sandbox root."
            )
        return target

    def read_text_file(self, relative_path: str, max_bytes: int = 64000) -> str:
        target = self._resolve_safe_path(relative_path)
        if not target.exists():
            return json.dumps({"error": f"File '{relative_path}' does not exist."})
        if not target.is_file():
            return json.dumps({"error": f"Path '{relative_path}' is a directory, not a file."})
        
        file_size = target.stat().st_size
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)
            
        truncated = file_size > max_bytes
        return json.dumps({
            "path": relative_path,
            "bytes_read": len(content.encode("utf-8")),
            "total_size_bytes": file_size,
            "truncated": truncated,
            "content": content
        })

    def write_text_file(self, relative_path: str, content: str) -> str:
        target = self._resolve_safe_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return json.dumps({"status": "success", "path": relative_path, "bytes_written": len(content.encode("utf-8"))})

# Verification
fs_sandbox = SandboxedFileSystem("/tmp/agent_workspace")
fs_sandbox.write_text_file("config/app.json", '{"environment": "production", "debug": false}')
print("Read Config:", fs_sandbox.read_text_file("config/app.json"))

try:
    fs_sandbox.read_text_file("../../etc/passwd")
except PermissionError as e:
    print("Security Guardrail Intercepted:", e)
