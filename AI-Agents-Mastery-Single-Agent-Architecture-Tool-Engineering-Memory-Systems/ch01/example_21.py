from pathlib import Path
from pydantic import BaseModel, Field

class SafeFileReaderArgs(BaseModel):
    relative_path: str = Field(description="Relative path within allowed sandbox root")

class SafeFileReader:
    def __init__(self, sandbox_root: Path):
        self.root = sandbox_root.resolve()

    def read_file(self, relative_path: str) -> str:
        target_path = (self.root / relative_path).resolve()
        # Security assertion: Target must remain strictly inside root
        if not str(target_path).startswith(str(self.root)):
            raise PermissionError("Access Denied: Path traversal detected outside sandbox root.")
        if not target_path.exists():
            return json.dumps({"error": f"File {relative_path} does not exist."})
        return target_path.read_text(encoding="utf-8")
