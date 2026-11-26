from pydantic import ValidationError

try:
    ResearchDAG(
        root_objective="Cyclic validation test objective",
        nodes=[
            SubQueryNode(node_id="n_a", query_text="query alpha", target_tiers=[SourceTier.PRIMARY_OFFICIAL], depends_on=["n_b"]),
            SubQueryNode(node_id="n_b", query_text="query beta", target_tiers=[SourceTier.PRIMARY_OFFICIAL], depends_on=["n_a"]),
        ],
    )
except ValidationError as exc:
    print(f"Caught expected cycle error: {exc.errors()[0]['msg']}")
