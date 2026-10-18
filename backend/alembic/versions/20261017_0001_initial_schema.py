"""Initial NusaMart schema from SQLAlchemy metadata.
Revision ID: 20261017_0001
Revises:
"""
revision = "20261017_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    from alembic import op
    from app.db.session import Base
    import app.models  # noqa: F401 - register all tables
    Base.metadata.create_all(bind=op.get_bind())

def downgrade() -> None:
    from alembic import op
    from app.db.session import Base
    import app.models  # noqa: F401
    Base.metadata.drop_all(bind=op.get_bind())
