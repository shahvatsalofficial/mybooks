dup_src = "def a():\n    return 1\n\ndef b():\n    return 1\n"
ambig = SearchReplaceEdit(
    edit_id="amb1",
    file_path="mod.py",
    target_symbol="a",
    search_block="    return 1",
    replace_block="    return 2",
    rationale="Update function a return value.",
)
res = apply_guarded_edit(dup_src, ambig)
assert not res.applied and "ambiguous" in res.error_reason
print(f"Rejected as expected: {res.error_reason}")
