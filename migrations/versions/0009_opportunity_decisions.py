"""Separate opportunity decision from measured outcome.

Revision ID: 0009_opportunity_decisions
Revises: 0008_no_show_interventions
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_opportunity_decisions"
down_revision = "0008_no_show_interventions"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("opportunities", sa.Column("decision_note", sa.Text(), nullable=True))
    op.add_column("opportunities", sa.Column("decided_by", sa.String(36), nullable=True))
    op.add_column("opportunities", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_opportunities_decided_by_users", "opportunities", "users", ["decided_by"], ["id"])
    op.create_index("ix_opportunities_decided_by", "opportunities", ["decided_by"])

def downgrade() -> None:
    op.drop_index("ix_opportunities_decided_by", table_name="opportunities")
    op.drop_constraint("fk_opportunities_decided_by_users", "opportunities", type_="foreignkey")
    op.drop_column("opportunities", "decided_at")
    op.drop_column("opportunities", "decided_by")
    op.drop_column("opportunities", "decision_note")
