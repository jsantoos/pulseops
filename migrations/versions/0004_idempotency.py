"""Deduplicate datasets/opportunities and add stable uniqueness constraints."""

from collections import defaultdict

from alembic import op
import sqlalchemy as sa

revision = "0004_idempotency"
down_revision = "0003_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    meta = sa.MetaData()
    datasets = sa.Table("datasets", meta, autoload_with=bind)
    opportunities = sa.Table("opportunities", meta, autoload_with=bind)
    outcomes = sa.Table("outcomes", meta, autoload_with=bind)

    # 1) Collapse duplicate logical opportunities, keeping the newest row.
    rows = bind.execute(
        sa.select(
            opportunities.c.id,
            opportunities.c.organization_id,
            opportunities.c.oie_opportunity_id,
            opportunities.c.created_at,
        ).order_by(opportunities.c.created_at.desc())
    ).mappings().all()
    keep_by_key: dict[tuple[str, str], str] = {}
    duplicate_opportunity_ids: list[str] = []
    for row in rows:
        key = (row["organization_id"], row["oie_opportunity_id"])
        if key not in keep_by_key:
            keep_by_key[key] = row["id"]
        else:
            duplicate_opportunity_ids.append(row["id"])
    if duplicate_opportunity_ids:
        bind.execute(
            sa.delete(outcomes).where(
                outcomes.c.opportunity_id.in_(duplicate_opportunity_ids)
            )
        )
        bind.execute(
            sa.delete(opportunities).where(
                opportunities.c.id.in_(duplicate_opportunity_ids)
            )
        )

    # 2) Collapse duplicate datasets by tenant + content hash. Any remaining
    # opportunity pointing at an older duplicate is re-pointed to the newest.
    dataset_rows = bind.execute(
        sa.select(
            datasets.c.id,
            datasets.c.organization_id,
            datasets.c.content_sha256,
            datasets.c.created_at,
        ).order_by(datasets.c.created_at.desc())
    ).mappings().all()
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in dataset_rows:
        grouped[(row["organization_id"], row["content_sha256"])].append(row["id"])
    for ids in grouped.values():
        if len(ids) < 2:
            continue
        keeper, *duplicates = ids
        bind.execute(
            sa.update(opportunities)
            .where(opportunities.c.dataset_id.in_(duplicates))
            .values(dataset_id=keeper)
        )
        bind.execute(sa.delete(datasets).where(datasets.c.id.in_(duplicates)))

    with op.batch_alter_table("datasets") as batch:
        batch.create_unique_constraint(
            "uq_dataset_org_content", ["organization_id", "content_sha256"]
        )
    with op.batch_alter_table("opportunities") as batch:
        batch.drop_constraint("uq_opportunity_dataset_oie", type_="unique")
        batch.create_unique_constraint(
            "uq_opportunity_org_oie", ["organization_id", "oie_opportunity_id"]
        )

    op.create_table(
        "opportunity_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.String(36),
            sa.ForeignKey("opportunities.id"),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("estimated_gain", sa.Float(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "opportunity_id", "dataset_id", name="uq_opportunity_snapshot_dataset"
        ),
    )
    op.create_index(
        "ix_opportunity_snapshots_opportunity_id",
        "opportunity_snapshots",
        ["opportunity_id"],
    )
    op.create_index(
        "ix_opportunity_snapshots_dataset_id", "opportunity_snapshots", ["dataset_id"]
    )
    op.create_index(
        "ix_opportunity_snapshots_opportunity_created",
        "opportunity_snapshots",
        ["opportunity_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("opportunity_snapshots")
    with op.batch_alter_table("opportunities") as batch:
        batch.drop_constraint("uq_opportunity_org_oie", type_="unique")
        batch.create_unique_constraint(
            "uq_opportunity_dataset_oie", ["dataset_id", "oie_opportunity_id"]
        )
    with op.batch_alter_table("datasets") as batch:
        batch.drop_constraint("uq_dataset_org_content", type_="unique")
