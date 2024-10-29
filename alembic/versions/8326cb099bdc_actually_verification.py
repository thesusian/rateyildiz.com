"""actually verification

Revision ID: 8326cb099bdc
Revises: b9dd80ca1717
Create Date: 2024-10-29 21:00:23.454629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8326cb099bdc'
down_revision: Union[str, None] = 'b9dd80ca1717'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
