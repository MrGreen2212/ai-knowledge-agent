"""add_conversations_and_messages_tables

Revision ID: 733548ba7c0c
Revises: ec90cfcc3d67
Create Date: 2026-08-01 00:39:28.441761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '733548ba7c0c'
down_revision: Union[str, Sequence[str], None] = 'ec90cfcc3d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Создание таблиц для системы истории диалогов.
    
    Создаются две таблицы:
    1. conversations - хранит информацию о диалогах
    2. messages - хранит сообщения в рамках диалогов
    """
    # Создание таблицы conversations
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True, comment='Название диалога (опционально, может генерироваться автоматически)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата и время создания диалога'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата и время последнего обновления диалога'),
        sa.PrimaryKeyConstraint('id'),
        comment='Таблица диалогов пользователя с AI ассистентом'
    )

    # Создание таблицы messages
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID диалога, к которому относится сообщение'),
        sa.Column('role', sa.String(length=20), nullable=False, comment="Роль отправителя: 'user' (пользователь) или 'assistant' (AI ассистент)"),
        sa.Column('content', sa.Text(), nullable=False, comment='Содержимое сообщения'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Дата и время создания сообщения'),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='ck_message_role'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Таблица сообщений в диалогах'
    )

    # Создание индексов для таблицы messages
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id'], unique=False)
    op.create_index('idx_messages_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)


def downgrade() -> None:
    """
    Откат миграции - удаление таблиц диалогов и сообщений.
    """
    # Удаление индексов
    op.drop_index('idx_messages_conversation_created', table_name='messages')
    op.drop_index('idx_messages_conversation', table_name='messages')
    
    # Удаление таблиц (messages первой из-за внешнего ключа)
    op.drop_table('messages')
    op.drop_table('conversations')
