class DeleteNoteInput(BaseModel):
    slug: str
    confirm: bool = Field(..., description="Must explicitly be set to true to execute deletion.")

@server.tool(name="delete_note", description="Permanently delete a note.")
def delete_note(params: DeleteNoteInput) -> str:
    if not params.confirm:
        return f"DeletionAborted: confirm parameter was false. Note '{params.slug}' was not deleted."
    if params.slug not in NOTES_DATABASE:
        return f"Error: Note '{params.slug}' does not exist."
    del NOTES_DATABASE[params.slug]
    return f"Success: Note '{params.slug}' permanently deleted."
