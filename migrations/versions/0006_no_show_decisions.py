"""Add operational recommendations and human decisions to no-show predictions."""
from alembic import op
import sqlalchemy as sa

revision = "0006_no_show_decisions"
down_revision = "0005_no_show_ml"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("no_show_predictions", sa.Column("recommended_action_type", sa.String(64), nullable=False, server_default="no_action"))
    op.add_column("no_show_predictions", sa.Column("recommended_action_label", sa.String(160), nullable=False, server_default="Apenas monitorar"))
    op.add_column("no_show_predictions", sa.Column("recommendation_reason", sa.Text(), nullable=False, server_default=""))
    op.add_column("no_show_predictions", sa.Column("risk_level", sa.String(32), nullable=False, server_default="low"))

    op.create_table(
        "no_show_prediction_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("prediction_id", sa.String(36), sa.ForeignKey("no_show_predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommended_action_type", sa.String(64), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("prediction_id", name="uq_no_show_prediction_decision_prediction"),
    )
    op.create_index("ix_no_show_prediction_decisions_organization_id", "no_show_prediction_decisions", ["organization_id"])
    op.create_index("ix_no_show_prediction_decisions_prediction_id", "no_show_prediction_decisions", ["prediction_id"])
    op.create_index("ix_no_show_prediction_decisions_decided_by", "no_show_prediction_decisions", ["decided_by"])
    op.create_index("ix_no_show_prediction_decisions_org_decided", "no_show_prediction_decisions", ["organization_id", "decided_at"])


def downgrade() -> None:
    op.drop_table("no_show_prediction_decisions")
    op.drop_column("no_show_predictions", "risk_level")
    op.drop_column("no_show_predictions", "recommendation_reason")
    op.drop_column("no_show_predictions", "recommended_action_label")
    op.drop_column("no_show_predictions", "recommended_action_type")
