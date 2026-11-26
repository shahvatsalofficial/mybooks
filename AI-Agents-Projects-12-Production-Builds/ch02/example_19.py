import ast

def find_unused_imports(source_code: str) -> list[str]:
    tree = ast.parse(source_code)
    imported: set[str] = set()
    used_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    imported.add(alias.asname or alias.name)
        elif isinstance(node, ast.Name):
            used_names.add(node.id)
    return sorted(imported - used_names)
