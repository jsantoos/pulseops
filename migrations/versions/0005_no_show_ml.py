"""Add model runs and no-show predictions for PulseOps Predict M7."""

from alembic import op
import sqlalchemy as sa

revision = "0005_no_show_ml"
down_revision = "0004_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("selected_model_version", sa.String(160), nullable=False),
        sa.Column("feature_set_version", sa.String(100), nullable=False),
        sa.Column("training_rows", sa.Integer(), nullable=False),
        sa.Column("calibration_rows", sa.Integer(), nullable=False),
        sa.Column("validation_rows", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_runs_organization_id", "model_runs", ["organization_id"])
    op.create_index("ix_model_runs_dataset_id", "model_runs", ["dataset_id"])
    op.create_index("ix_model_runs_org_created", "model_runs", ["organization_id", "created_at"])

    op.create_table(
        "no_show_predictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("model_run_id", sa.String(36), sa.ForeignKey("model_runs.id"), nullable=False),
        sa.Column("appointment_id", sa.String(100), nullable=False),
        sa.Column("equipment_id", sa.String(100), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("expected_revenue", sa.Float(), nullable=False),
        sa.Column("expected_loss", sa.Float(), nullable=False),
        sa.Column("expected_recovered_revenue", sa.Float(), nullable=False),
        sa.Column("expected_net_value", sa.Float(), nullable=False),
        sa.Column("action_recommended", sa.Boolean(), nullable=False),
        sa.Column("model_version", sa.String(160), nullable=False),
        sa.Column("feature_set_version", sa.String(100), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("model_run_id", "appointment_id", name="uq_no_show_prediction_run_appointment"),
    )
    op.create_index("ix_no_show_predictions_organization_id", "no_show_predictions", ["organization_id"])
    op.create_index("ix_no_show_predictions_dataset_id", "no_show_predictions", ["dataset_id"])
    op.create_index("ix_no_show_predictions_model_run_id", "no_show_predictions", ["model_run_id"])
    op.create_index("ix_no_show_predictions_appointment_id", "no_show_predictions", ["appointment_id"])
    op.create_index("ix_no_show_predictions_org_probability", "no_show_predictions", ["organization_id", "probability"])


def downgrade() -> None:
    op.drop_table("no_show_predictions")
    op.drop_table("model_runs")
