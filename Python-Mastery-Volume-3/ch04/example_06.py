class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    version_id: Mapped[int] = mapped_column(default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id,
    }
