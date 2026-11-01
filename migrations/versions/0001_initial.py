"""Initial PulseOps application schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("organizations", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("datasets", sa.Column("id", sa.String(36), primary_key=True), sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("filename", sa.String(255), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("content_sha256", sa.String(64), nullable=False), sa.Column("raw_payload", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_datasets_organization_id", "datasets", ["organization_id"])
    op.create_table("opportunities", sa.Column("id", sa.String(36), primary_key=True), sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False), sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False), sa.Column("oie_opportunity_id", sa.String(64), nullable=False), sa.Column("category", sa.String(64), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("severity", sa.String(32), nullable=False), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("estimated_gain", sa.Float(), nullable=False), sa.Column("score", sa.Float(), nullable=False), sa.Column("recommended_actions", sa.JSON(), nullable=False), sa.Column("evidence", sa.JSON(), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("dataset_id", "oie_opportunity_id", name="uq_opportunity_dataset_oie"))
    op.create_index("ix_opportunities_organization_id", "opportunities", ["organization_id"])
    op.create_index("ix_opportunities_dataset_id", "opportunities", ["dataset_id"])
    op.create_index("ix_opportunities_oie_opportunity_id", "opportunities", ["oie_opportunity_id"])
    op.create_index("ix_opportunities_org_score", "opportunities", ["organization_id", "score"])
    op.create_table("outcomes", sa.Column("id", sa.String(36), primary_key=True), sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False), sa.Column("action_taken", sa.Boolean(), nullable=False), sa.Column("measured_gain", sa.Float(), nullable=True), sa.Column("notes", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("opportunity_id"))
    op.create_index("ix_outcomes_opportunity_id", "outcomes", ["opportunity_id"], unique=True)


def downgrade() -> None:
    op.drop_table("outcomes")
    op.drop_table("opportunities")
    op.drop_table("datasets")
    op.drop_table("organizations")
