"""add username field

Revision ID: add_username_field
Revises: add_user_fields
Create Date: 2024-05-26 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_username_field'
down_revision = 'add_user_fields'
branch_labels = None
depends_on = None

def upgrade():
    # 添加 username 字段
    op.add_column('users', sa.Column('username', sa.String(50), nullable=True))
    
    # 创建唯一索引
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # 更新现有用户的 username（使用 email 的前缀作为临时用户名）
    op.execute("""
        UPDATE users 
        SET username = SUBSTRING_INDEX(email, '@', 1)
        WHERE username IS NULL
    """)
    
    # 将 username 设置为非空
    op.alter_column('users', 'username',
                    existing_type=sa.String(50),
                    nullable=False)

def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_users_username'), table_name='users')
    
    # 删除 username 字段
    op.drop_column('users', 'username') 