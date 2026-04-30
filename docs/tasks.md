# Task List

Task state = section position. No checkbox marks.
Transitions: Backlog → In Progress (before coding) → Done (after commit).
Max 1 task in In Progress at a time.
Completed tasks are archived in `docs/tasks_done.md`.

---

## In Progress

#### Ops — フロントエンド Docker パイプラインの統一

**目的:** フロントエンドのコンテナイメージビルドをGitHub Runner上に移し、
バックエンドパイプライン（docker build → Artifact Registry push → VM pull）と一貫させる。

**修正対象:**
- `frontend/Dockerfile` — マルチステージビルド化（Node.js で React ビルド → nginx）
- `docker-compose.yml` — `image:` フィールドを追加（`FRONTEND_IMAGE` 環境変数で切り替え）
- `.github/workflows/deploy.yml` — フロントエンドジョブを npm build/SCP/VM build から GCP Auth/Docker build+push/VM pull に変更
- `.env.example` — `FRONTEND_IMAGE` を追記

---

## Backlog

#### Phase 39 — TradeDetailPage FoCheck 結果表示の不具合修正

**目的:** `frontend/src/pages/TradeDetailPage.tsx` において、
FoCheck が未実行のときも・実行済みでエラーなしのときも、
同じメッセージ `"No FoCheck failures found. Run FoCheck first."` が表示される不具合を修正する。

**修正内容:**
- FoCheck 未実行（`fo_check_results` が null / 未設定）の場合: `"FoCheck has not been run yet."` を表示
- FoCheck 実行済みで全ルール合格の場合: `"All FoCheck rules passed."` を表示
- FoCheck 実行済みで失敗あり: 失敗ルール一覧を表示（既存ロジック）

---

#### Phase 36 — FO/BO エージェントのツール一覧確認画面

**目的:** FO エージェントと BO エージェントがそれぞれ利用できるツールを一覧で確認できる画面を作成する。

**Frontend:**
- `frontend/src/pages/AgentToolsPage.tsx` 新規作成
  - FO エージェント用ツール一覧テーブル（ツール名・説明・HITL 対象か否か）
  - BO エージェント用ツール一覧テーブル（同上）
  - NavBar に "Agent Tools" リンク追加

**Backend:**
- `GET /api/v1/agent-tools` エンドポイント追加
  - FO/BO エージェントが保持するツール定義（name, description, is_hitl）を返却

---

#### Phase 40 — EventPending ステータス時の Triage ボタン非活性化

**目的:** `EventPending` ステータスの取引に対して FO Triage・BO Triage をマニュアル実行できないよう、
`Start FO Triage` / `Start BO Triage` ボタンを disabled にする。

**修正内容:**
- `frontend/src/pages/TradeDetailPage.tsx` の Triage 起動ボタンに
  `workflow_status === 'EventPending'` のときは `disabled` 属性を付与
- ボタン非活性時はツールチップ等で理由を表示（例: `"Cannot start triage while event is pending"`）

---

#### Phase 28 — 取引入力画面：Counterparty 検索モーダル

**目的:** 取引入力フォームの Counterparty 選択をプルダウンからモーダル検索に変更する。
現状はプルダウンに全件ロードしているため、件数が増えると使いにくい。

**Frontend:**
- `frontend/src/pages/TradeInputPage.tsx` 更新
  - Counterparty フィールドを `<select>` から「選択済み表示 + 変更ボタン」に変更
  - ボタン押下でモーダルを開く
  - モーダル内: 名前前方一致・LEI 部分一致などで検索 → 結果一覧から1件選択
  - 選択後モーダルを閉じ、フォームに LEI + 名前を反映
- API: `GET /api/v1/counterparties?name=<prefix>&lei=<partial>` を活用（既存エンドポイント）

---

#### Phase 12 — MCP Server Externalization（低優先度）

- `tools.py` の tool 実装を MCP サーバとして外部化
- LangGraph agent を MCP クライアントとして接続するよう変更
- MCPサーバのDockerコンテナ化
- MCPサーバの認証・認可設計

---

#### Phase 13 — deepagents版（Future）

> LangGraph版完成後に実装。同じユースケースを deepagents で実装し、
> コード量・HITL API・ツール管理の違いを比較する。

- Add `deepagents>=0.5.0a4` and `langchain>=1.2.15` to `pyproject.toml`
- Implement `build_deep_graph()` (`src/infrastructure/agent_deep.py`)
- Implement `TriageDeepSTPFailureUseCase` (`src/infrastructure/triage_use_case_deep.py`)
- Implement `POST /api/v1/triage/deep` + resume endpoint (`src/presentation/router_deep.py`)
- Add `docs/comparison.md` — LangGraph vs deepagents comparison

---

#### Phase 21 — GCP read-only IAM ロールと MCP 連携（低優先度・保留）

> **保留理由**: Web版 Claude Code は Anthropic の VM 上で動作するため、GCP サービスアカウントキーを
> そこに置くことはセキュリティ上好ましくない。
> デスクトップ版 Claude Code を使う環境が整ったタイミングで再検討する。

- GCP サービスアカウント `claude-reader` 作成済み
  - 付与ロール: `roles/compute.viewer`, `roles/logging.viewer`, `roles/monitoring.viewer`, `roles/run.viewer`
- 残り作業: `~/.claude/settings.json` に `GOOGLE_APPLICATION_CREDENTIALS` を設定（デスクトップ版環境で実施）

---

#### Phase 23 — フロントエンドを Firebase Hosting に移行（低優先度）

> Phase 20（Cloud Run 移行）と Phase 22（CI/CD）完了後に検討。

- Firebase プロジェクトを作成（GCP プロジェクトと連携可能）
- `firebase.json` と `.firebaserc` を追加
- SPA ルーティング対応: `firebase.json` に `"rewrites": [{"source": "**", "destination": "/index.html"}]` を設定
- CI/CD への組み込み: GitHub Actions に `firebase-action/deploy` ステップを追加

---

#### Ops — GCP 静的外部 IP の予約（人間作業）

> VM を再起動するたびに外部 IP が変わる問題の恒久対策。

```bash
gcloud compute addresses create stp-agent-ip --region=us-central1
gcloud compute instances add-access-config free-dev-vm \
  --access-config-name="External NAT" --address=<IP> --zone=us-central1-a
```

完了後は `.env` の `VITE_API_URL` と `CORS_ORIGINS` を新しい固定 IP に更新する。
