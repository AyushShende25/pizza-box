"""change payment-method-enum

Revision ID: 36e049d461ad
Revises: 62aff7beb847
Create Date: 2025-11-11 23:13:08.697043

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "36e049d461ad"
down_revision: Union[str, Sequence[str], None] = "62aff7beb847"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1. Rename the existing enum type to keep it as a backup
    op.execute("ALTER TYPE paymentmethod RENAME TO paymentmethod_old;")

    # Step 2. Create the new enum type
    op.execute("CREATE TYPE paymentmethod AS ENUM ('COD', 'DIGITAL');")

    # Step 3. Alter the column to use the new enum
    op.execute(
        """
        ALTER TABLE orders 
        ALTER COLUMN payment_method 
        TYPE paymentmethod 
        USING payment_method::text::paymentmethod;
        """
    )

    # Step 4. Drop the old enum
    op.execute("DROP TYPE paymentmethod_old;")


def downgrade() -> None:
    # Recreate old enum for rollback
    op.execute("CREATE TYPE paymentmethod_old AS ENUM ('COD', 'CARD', 'UPI');")

    op.execute(
        """
        ALTER TABLE orders 
        ALTER COLUMN payment_method 
        TYPE paymentmethod_old 
        USING payment_method::text::paymentmethod_old;
        """
    )

    op.execute("DROP TYPE paymentmethod;")
    op.execute("ALTER TYPE paymentmethod_old RENAME TO paymentmethod;")
