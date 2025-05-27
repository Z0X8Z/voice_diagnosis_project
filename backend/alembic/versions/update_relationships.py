"""update relationships

Revision ID: update_relationships
Revises: add_username_field
Create Date: 2024-05-26 20:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_relationships'
down_revision = 'add_username_field'
branch_labels = None
depends_on = None

def upgrade():
    # 确保外键约束存在
    op.create_foreign_key(
        'fk_voice_metrics_user_id_users',
        'voice_metrics', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_diagnosis_sessions_user_id_users',
        'diagnosis_sessions', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_voice_metrics_user_id_users', 'voice_metrics', type_='foreignkey')
    op.drop_constraint('fk_diagnosis_sessions_user_id_users', 'diagnosis_sessions', type_='foreignkey') 