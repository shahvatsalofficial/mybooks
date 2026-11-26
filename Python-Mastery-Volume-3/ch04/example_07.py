# Pessimistic lock with fail-fast semantics
stmt = (
    select(AccountModel)
    .where(AccountModel.id == account_id)
    .with_for_update(nowait=True)
)
