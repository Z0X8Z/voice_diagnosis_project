"""add user fields

Revision ID: add_user_fields
Revises: 1be8ff42b15b
Create Date: 2024-05-26 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_user_fields'
down_revision = '1be8ff42b15b'
branch_labels = None
depends_on = None

def upgrade():
    # 删除现有表
    op.drop_table('diagnosis_sessions')
    op.drop_table('voice_metrics')
    op.drop_table('users')
    
    # 重新创建用户表
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # 重新创建语音指标表
    op.create_table('voice_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('mfcc_1', sa.Float(), nullable=True),
        sa.Column('mfcc_2', sa.Float(), nullable=True),
        sa.Column('mfcc_3', sa.Float(), nullable=True),
        sa.Column('mfcc_4', sa.Float(), nullable=True),
        sa.Column('mfcc_5', sa.Float(), nullable=True),
        sa.Column('mfcc_6', sa.Float(), nullable=True),
        sa.Column('mfcc_7', sa.Float(), nullable=True),
        sa.Column('mfcc_8', sa.Float(), nullable=True),
        sa.Column('mfcc_9', sa.Float(), nullable=True),
        sa.Column('mfcc_10', sa.Float(), nullable=True),
        sa.Column('mfcc_11', sa.Float(), nullable=True),
        sa.Column('mfcc_12', sa.Float(), nullable=True),
        sa.Column('mfcc_13', sa.Float(), nullable=True),
        sa.Column('chroma_1', sa.Float(), nullable=True),
        sa.Column('chroma_2', sa.Float(), nullable=True),
        sa.Column('chroma_3', sa.Float(), nullable=True),
        sa.Column('chroma_4', sa.Float(), nullable=True),
        sa.Column('chroma_5', sa.Float(), nullable=True),
        sa.Column('chroma_6', sa.Float(), nullable=True),
        sa.Column('chroma_7', sa.Float(), nullable=True),
        sa.Column('chroma_8', sa.Float(), nullable=True),
        sa.Column('chroma_9', sa.Float(), nullable=True),
        sa.Column('chroma_10', sa.Float(), nullable=True),
        sa.Column('chroma_11', sa.Float(), nullable=True),
        sa.Column('chroma_12', sa.Float(), nullable=True),
        sa.Column('rms', sa.Float(), nullable=True),
        sa.Column('zcr', sa.Float(), nullable=True),
        sa.Column('mel_spectrogram', sa.Text(), nullable=True),
        sa.Column('model_prediction', sa.String(50), nullable=True),
        sa.Column('model_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 重新创建诊断会话表
    op.create_table('diagnosis_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analysis_progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('diagnosis_suggestion', sa.Text(), nullable=True),
        sa.Column('follow_up_questions', sa.Text(), nullable=True),
        sa.Column('conversation_history', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('diagnosis_sessions')
    op.drop_table('voice_metrics')
    op.drop_table('users') 