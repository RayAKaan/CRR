"""phase 5 transaction integrity constraints

Revision ID: l3a4b5c6d7e8
Revises: k2f3a4b5c6d7
Create Date: 2026-11-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "k2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_transaction_reservations_reservation",
        table_name="transaction_reservations",
    )
    op.create_index(
        "uq_transaction_reservations_org_reservation",
        "transaction_reservations",
        ["organization_id", "reservation_id"],
        unique=True,
    )
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.add_column(sa.Column("offer_id", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("offer_version", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("opportunity_version", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE transactions
            SET
                offer_id = (
                    SELECT agreements.offer_id
                    FROM agreements
                    WHERE agreements.organization_id = transactions.organization_id
                      AND agreements.id = transactions.agreement_id
                ),
                offer_version = (
                    SELECT agreements.offer_version
                    FROM agreements
                    WHERE agreements.organization_id = transactions.organization_id
                      AND agreements.id = transactions.agreement_id
                ),
                opportunity_version = (
                    SELECT offers.opportunity_version
                    FROM agreements
                    JOIN offers
                      ON offers.organization_id = agreements.organization_id
                     AND offers.id = agreements.offer_id
                    WHERE agreements.organization_id = transactions.organization_id
                      AND agreements.id = transactions.agreement_id
                )
            """
        )
    )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "offer_id",
            existing_type=sa.String(length=80),
            nullable=False,
        )
        batch_op.alter_column(
            "offer_version",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "opportunity_version",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_transactions_org_offer",
            "offers",
            ["organization_id", "offer_id"],
            ["organization_id", "id"],
        )
        batch_op.create_check_constraint(
            "ck_transactions_quantity_positive",
            "quantity_value > 0",
        )
        batch_op.create_check_constraint(
            "ck_transactions_price_nonnegative",
            "price >= 0",
        )
        batch_op.create_check_constraint(
            "ck_transactions_resource_version_positive",
            "resource_version >= 1",
        )
        batch_op.create_check_constraint(
            "ck_transactions_offer_version_positive",
            "offer_version >= 1",
        )
        batch_op.create_check_constraint(
            "ck_transactions_opportunity_version_positive",
            "opportunity_version >= 1",
        )
        batch_op.create_check_constraint(
            "ck_transactions_version_positive",
            "version >= 1",
        )
        batch_op.create_check_constraint(
            "ck_transactions_parties_distinct",
            "proposer_actor_id <> recipient_actor_id",
        )
        batch_op.create_check_constraint(
            "ck_transactions_status",
            "status IN ('AGREED', 'SCHEDULED', 'DISPUTED', 'CANCELLED')",
        )
        batch_op.create_check_constraint(
            "ck_transactions_schedule_consistency",
            "status != 'SCHEDULED' OR scheduled_for IS NOT NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("ck_transactions_schedule_consistency", type_="check")
        batch_op.drop_constraint("ck_transactions_status", type_="check")
        batch_op.drop_constraint("ck_transactions_parties_distinct", type_="check")
        batch_op.drop_constraint("ck_transactions_version_positive", type_="check")
        batch_op.drop_constraint("ck_transactions_opportunity_version_positive", type_="check")
        batch_op.drop_constraint("ck_transactions_offer_version_positive", type_="check")
        batch_op.drop_constraint("ck_transactions_resource_version_positive", type_="check")
        batch_op.drop_constraint("ck_transactions_price_nonnegative", type_="check")
        batch_op.drop_constraint("ck_transactions_quantity_positive", type_="check")
        batch_op.drop_constraint("fk_transactions_org_offer", type_="foreignkey")
        batch_op.drop_column("opportunity_version")
        batch_op.drop_column("offer_version")
        batch_op.drop_column("offer_id")
    op.drop_index(
        "uq_transaction_reservations_org_reservation",
        table_name="transaction_reservations",
    )
    op.create_index(
        "ix_transaction_reservations_reservation",
        "transaction_reservations",
        ["organization_id", "reservation_id"],
    )
