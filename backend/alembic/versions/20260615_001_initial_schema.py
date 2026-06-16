"""Initial schema — all 7 tables.

Revision ID: 001_initial
Revises: None
Create Date: 2026-06-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True, default=None),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("credits", sa.Integer, default=10),
        sa.Column("referral_code", sa.String(32), unique=True, nullable=True, index=True),
        sa.Column("referred_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("token_version", sa.Integer, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_check_constraint("ck_users_credits_non_negative", "users", "credits >= 0")

    # ── image_generations ────────────────────────────────────────────────
    op.create_table(
        "image_generations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("negative_prompt", sa.Text, default=""),
        sa.Column("model", sa.String(100), default="agnes-image-2.1-flash"),
        sa.Column("size", sa.String(20), default="1024x768"),
        sa.Column("style", sa.String(100), default="none"),
        sa.Column("seed", sa.Integer, nullable=True),
        sa.Column("steps", sa.Integer, default=30),
        sa.Column("cfg_scale", sa.Float, default=7.5),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), default="completed"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("parameters", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── video_generations ────────────────────────────────────────────────
    op.create_table(
        "video_generations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("negative_prompt", sa.Text, default=""),
        sa.Column("model", sa.String(100), default="agnes-video-v2.0"),
        sa.Column("num_frames", sa.Integer, default=121),
        sa.Column("frame_rate", sa.Integer, default=24),
        sa.Column("width", sa.Integer, default=1152),
        sa.Column("height", sa.Integer, default=768),
        sa.Column("seed", sa.Integer, nullable=True),
        sa.Column("style", sa.String(100), default="cinematic"),
        sa.Column("task_id", sa.String(200), nullable=True),
        sa.Column("video_id", sa.String(500), nullable=True, index=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), default="queued"),
        sa.Column("progress", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("credits_charged", sa.Integer, default=0, nullable=False),
        sa.Column("parameters", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── gallery_items ────────────────────────────────────────────────────
    op.create_table(
        "gallery_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, default=""),
        sa.Column("media_type", sa.String(20)),
        sa.Column("media_url", sa.String(500), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("style", sa.String(100), default=""),
        sa.Column("tags", sa.JSON, default=list),
        sa.Column("is_public", sa.Boolean, default=True, index=True),
        sa.Column("likes", sa.Integer, default=0),
        sa.Column("views", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── gallery_likes ────────────────────────────────────────────────────
    op.create_table(
        "gallery_likes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("gallery_items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_gallery_like_user_item", "gallery_likes", ["user_id", "item_id"])

    # ── api_keys ─────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("key", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("rate_limit", sa.Integer, default=10),
        sa.Column("daily_limit", sa.Integer, default=100),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── credit_transactions ──────────────────────────────────────────────
    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("balance_after", sa.Integer, nullable=False),
        sa.Column("type", sa.String(32), nullable=False, index=True),
        sa.Column("ref_type", sa.String(32), nullable=True),
        sa.Column("ref_id", sa.Integer, nullable=True),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("credit_transactions")
    op.drop_table("api_keys")
    op.drop_table("gallery_likes")
    op.drop_table("gallery_items")
    op.drop_table("video_generations")
    op.drop_table("image_generations")
    op.drop_constraint("ck_users_credits_non_negative", "users", type_="check")
    op.drop_table("users")
