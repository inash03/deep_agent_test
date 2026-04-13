"""SQLAlchemy engine / session factory.

使い方:
  # FastAPI の Depends で1リクエスト1セッション
  def my_endpoint(db: Session = Depends(get_db)):
      ...

  # 手動で使う場合
  with make_session() as db:
      db.add(...)
      db.commit()

NOTE: ENGINE は DATABASE_URL 環境変数から遅延初期化される（import 時には作らない）。
      これにより、DB が不要な単体テストでも import できる。
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_engine():
    global _engine
    if _engine is None:
        url = os.environ["DATABASE_URL"]
        _engine = create_engine(
            url,
            pool_pre_ping=True,  # 接続が切れていたら自動再接続
        )
    return _engine


def make_session() -> Session:
    """新しいセッションを返す。呼び出し元が close() する責任を持つ。"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal()


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends 用ジェネレータ。リクエスト終了時に自動 close。

    使用例:
      @router.get("/foo")
      def foo(db: Session = Depends(get_db)):
          ...
    """
    db = make_session()
    try:
        yield db
    finally:
        db.close()
