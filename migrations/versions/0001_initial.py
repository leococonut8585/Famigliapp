"""Initial migration.

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=64), nullable=False, unique=True),
        sa.Column('password', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, default='user'),
        sa.Column('email', sa.String(length=120)),
        sa.Column('A', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('O', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_table(
        'point_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('delta_a', sa.Integer(), nullable=False),
        sa.Column('delta_o', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'post',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('category', sa.String(length=64)),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table('post')
    op.drop_table('point_history')
    op.drop_table('user')
