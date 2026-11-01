"""Add structured intervention workflow for no-show recommendations."""
from alembic import op
import sqlalchemy as sa

revision = "0008_no_show_interventions"
down_revision = "0007_no_show_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "no_show_interventions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("prediction_id", sa.String(36), sa.ForeignKey("no_show_predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("contact_result", sa.String(32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("executed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("prediction_id", name="uq_no_show_intervention_prediction"),
    )
    op.create_index("ix_no_show_interventions_organization_id", "no_show_interventions", ["organization_id"])
    op.create_index("ix_no_show_interventions_prediction_id", "no_show_interventions", ["prediction_id"])
    op.create_index("ix_no_show_interventions_executed_by", "no_show_interventions", ["executed_by"])
    op.create_index("ix_no_show_interventions_org_executed", "no_show_interventions", ["organization_id", "executed_at"])

    # Preserve prior Measure test/history. Earlier versions only knew that an
    # intervention happened, not how. Mark those as legacy/other rather than
    # losing the execution lineage.
    op.execute(sa.text("""
        INSERT INTO no_show_interventions (
            id, organization_id, prediction_id, channel, contact_result,
            note, executed_by, executed_at, created_at, updated_at
        )
        SELECT
            id, organization_id, prediction_id, 'other', 'other',
            COALESCE(note, 'Intervenção migrada do fluxo Measure anterior.'),
            recorded_by, updated_at, created_at, updated_at
        FROM no_show_prediction_outcomes
        WHERE intervention_executed = true
        ON CONFLICT (prediction_id) DO NOTHING
    """))


def downgrade() -> None:
    op.drop_table("no_show_interventions")
