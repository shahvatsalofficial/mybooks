class DeleteNoteInput(BaseModel):
    slug: str = Field(..., min_length=1, description="Slug identifier of the note to remove.")

@mcp.tool()
async def delete_note(params: DeleteNoteInput, ctx: Context) -> str:
    db: aiosqlite.Connection = ctx.request_context.lifespan_context["db"]
    sys.stderr.write(f"[Tools] Attempting deletion of note '{params.slug}'...\n")

    async with db.execute("SELECT slug FROM notes WHERE slug = ?", (params.slug,)) as cursor:
        row = await cursor.fetchone()

    if not row:
        # Raise KeyError or return descriptive error
        raise KeyError(f"Note '{params.slug}' does not exist; cannot delete.")

    await db.execute("DELETE FROM notes WHERE slug = ?", (params.slug,))
    await db.commit()

    return f"Note '{params.slug}' successfully deleted from storage."
