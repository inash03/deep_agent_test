"""Alembic 実行環境の設定ファイル。

このファイルは alembic コマンドが実行されるたびに読み込まれる。
主な役割:
  1. DATABASE_URL 環境変数から DB 接続文字列を取得
  2. SQLAlchemy モデルの metadata を Alembic に登録
     （これにより --autogenerate がモデルとDBを比較できる）
  3. offline/online モードで migration を実行

offline モード  — DB接続なしで SQL スクリプトを生成（CI/CDで使うことも）
online モード   — 実際にDBに接続して migration を実行（通常はこちら）
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# alembic.ini のログ設定を適用
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------
# IMPORTANT: ここで全モデルを import する
# Alembic が Base.metadata を通じてテーブル定義を認識する
# 新しいモデルを追加したら必ずここに import を追加すること
# ------------------------------------------------------------
from src.infrastructure.db.models import Base  # noqa: E402

target_metadata = Base.metadata

# DATABASE_URL 環境変数で sqlalchemy.url を上書き（alembic.ini の placeholder を置き換える）
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """offline モード: DB に接続せず SQL スクリプトを標準出力に書き出す。

    使用例: alembic upgrade head --sql > migration.sql
    本番環境で DBA が SQL を確認・実行したい場合に有用。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """online モード: DB に実際に接続して migration を実行する。

    通常の alembic upgrade head はこちらが呼ばれる。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # migration 実行後は接続をプールしない
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
