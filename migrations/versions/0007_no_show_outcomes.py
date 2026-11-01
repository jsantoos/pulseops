"""Add measured outcomes for no-show recommendations."""
from alembic import op
import sqlalchemy as sa

revision = "0007_no_show_outcomes"
down_revision = "0006_no_show_decisions"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "no_show_prediction_outcomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("prediction_id", sa.String(36), sa.ForeignKey("no_show_predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intervention_executed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("observed_status", sa.String(32), nullable=True),
        sa.Column("realized_revenue", sa.Float(), nullable=True),
        sa.Column("measured_recovered_value", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("prediction_id", name="uq_no_show_prediction_outcome_prediction"),
    )
    op.create_index("ix_no_show_prediction_outcomes_organization_id", "no_show_prediction_outcomes", ["organization_id"])
    op.create_index("ix_no_show_prediction_outcomes_prediction_id", "no_show_prediction_outcomes", ["prediction_id"])
    op.create_index("ix_no_show_prediction_outcomes_recorded_by", "no_show_prediction_outcomes", ["recorded_by"])
    op.create_index("ix_no_show_prediction_outcomes_org_updated", "no_show_prediction_outcomes", ["organization_id", "updated_at"])

def downgrade() -> None:
    op.drop_table("no_show_prediction_outcomes")
