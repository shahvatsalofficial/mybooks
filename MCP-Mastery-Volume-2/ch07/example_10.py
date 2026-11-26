# FLAWED VALIDATION CODE
if not requested_path.startswith("/data/scratch"):
    requested_path = os.path.join("/data/scratch", requested_path)
with open(requested_path, "r") as f:
    return f.read()
