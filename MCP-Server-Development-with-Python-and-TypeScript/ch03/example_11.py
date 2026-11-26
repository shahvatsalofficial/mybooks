@server.resource("memo://notes/filter{?tag}")
def filter_notes_by_tag(tag: str = "") -> str:
    """Filter notes catalog by a specific tag query parameter."""
    matching = {
        k: v for k, v in NOTES_STORE.items()
        if not tag or tag.lower() in [t.lower() for t in v["tags"]]
    }
    return json.dumps(matching, indent=2)
