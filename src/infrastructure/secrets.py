"""シークレット取得の抽象化レイヤー。

SECRET_BACKEND 環境変数で参照先を切り替える:

  SECRET_BACKEND=env  (デフォルト)
    → os.environ から読む（load_dotenv() で .env を読み込み済みの前提）
    → ローカル開発・Docker Compose 環境向け

  SECRET_BACKEND=gcp
    → GCP Secret Manager から取得して os.environ に注入する
    → GCP VM 本番環境向け
    → 要: pip install -e ".[gcp]" + GCP_PROJECT_ID 環境変数

使い方（main.py で1回だけ呼ぶ）:
  load_dotenv()           # .env から SECRET_BACKEND / GCP_PROJECT_ID を読む
  load_secrets()          # シークレットを取得して os.environ に注入

切り替え方:
  .env に SECRET_BACKEND=env  → .env 内の値を使う（デフォルト）
  .env に SECRET_BACKEND=gcp  → GCP Secret Manager から取得

注意:
  SECRET_BACKEND と GCP_PROJECT_ID はシークレットではなく設定値なので
  .env に書いても問題ない。
"""

from __future__ import annotations

import logging
import os

_logger = logging.getLogger("stp_triage.secrets")

# ---------------------------------------------------------------------------
# シークレットマッピング
#   キー   : os.environ に注入する環境変数名
#   値     : GCP Secret Manager 上のシークレット名
#
# GCP 側でシークレットを作成するときの名前はこのマッピングの値に合わせること。
# 例: gcloud secrets create anthropic-api-key --replication-policy=automatic
# ---------------------------------------------------------------------------
_SECRET_MAP: dict[str, str] = {
    "ANTHROPIC_API_KEY": "anthropic-api-key",
    "DATABASE_URL": "database-url",
}


def load_secrets() -> None:
    """SECRET_BACKEND に応じてシークレットを取得し os.environ に注入する。

    アプリ起動時に1回だけ呼ぶこと。
    load_dotenv() の後に呼ぶことで、SECRET_BACKEND 自体を .env から読める。
    """
    backend = os.environ.get("SECRET_BACKEND", "env").strip().lower()

    if backend == "gcp":
        _load_from_gcp()
    elif backend == "env":
        _load_from_env()
    else:
        raise ValueError(
            f"Unknown SECRET_BACKEND={backend!r}. "
            "Valid values: 'env' (default) or 'gcp'."
        )


# ---------------------------------------------------------------------------
# backend: env
# ---------------------------------------------------------------------------

def _load_from_env() -> None:
    """環境変数（.env ファイル）からシークレットを読む。

    load_dotenv() が既に os.environ に展開済みなので追加の処理は不要。
    未設定のキーがあれば警告を出すだけ。
    """
    _logger.info("secrets backend: env (.env file / environment variables)")

    missing = [key for key in _SECRET_MAP if not os.environ.get(key)]
    if missing:
        _logger.warning(
            "the following secrets are not set in environment: %s",
            missing,
        )


# ---------------------------------------------------------------------------
# backend: gcp
# ---------------------------------------------------------------------------

def _load_from_gcp() -> None:
    """GCP Secret Manager からシークレットを取得し os.environ に注入する。

    前提条件:
      - pip install -e ".[gcp]" (google-cloud-secret-manager が必要)
      - GCP_PROJECT_ID 環境変数が設定されていること
      - VM のサービスアカウントに roles/secretmanager.secretAccessor が付与済み
        （GCP VM 上では Application Default Credentials が自動で使われる）

    GCP コンソールでの事前準備:
      1. Secret Manager API を有効化
      2. 各シークレットを作成（名前は _SECRET_MAP の値に合わせる）
      3. VM のサービスアカウントに Secret Manager Secret Accessor ロールを付与
    """
    try:
        from google.cloud import secretmanager  # type: ignore[import-untyped]
    except ImportError:
        raise RuntimeError(
            "SECRET_BACKEND=gcp には google-cloud-secret-manager が必要です。\n"
            "  pip install -e '.[gcp]'\n"
            "または\n"
            "  pip install google-cloud-secret-manager"
        ) from None

    project_id = os.environ.get("GCP_PROJECT_ID", "").strip()
    if not project_id:
        raise RuntimeError(
            "SECRET_BACKEND=gcp には GCP_PROJECT_ID 環境変数が必要です。\n"
            ".env に GCP_PROJECT_ID=your-project-id を追加してください。"
        )

    _logger.info(
        "secrets backend: GCP Secret Manager (project=%s)", project_id
    )

    client = secretmanager.SecretManagerServiceClient()

    for env_key, secret_name in _SECRET_MAP.items():
        # 既に環境変数に値がある場合はスキップ
        # → ローカルで一部だけ上書きしたい場合に便利
        if os.environ.get(env_key):
            _logger.debug(
                "skipping %s (already set in environment, not overwriting)",
                env_key,
            )
            continue

        resource_name = (
            f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        )
        try:
            response = client.access_secret_version(
                request={"name": resource_name}
            )
            value = response.payload.data.decode("utf-8").strip()
            os.environ[env_key] = value
            _logger.info("loaded secret: %s", env_key)
        except Exception as exc:
            raise RuntimeError(
                f"GCP Secret Manager からのシークレット取得に失敗しました。\n"
                f"  環境変数名 : {env_key}\n"
                f"  シークレット名: {secret_name}\n"
                f"  プロジェクト : {project_id}\n"
                f"  エラー      : {exc}\n\n"
                "確認事項:\n"
                "  1. GCP コンソールでシークレットが作成されているか\n"
                "  2. VM のサービスアカウントに "
                "roles/secretmanager.secretAccessor が付与されているか\n"
                "  3. Secret Manager API が有効化されているか"
            ) from exc
