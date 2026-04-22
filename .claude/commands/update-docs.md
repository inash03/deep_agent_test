README.md / docs/architecture.md / docs/requirements.md を最新コードに同期してください。

## 背景

大きなファイルを1レスポンスで生成すると "API Error: Stream idle timeout" が発生する。
3ファイルを独立したサブエージェントに **並列** 委譲することで回避する。

## 手順

1. `docs/progress.md`（直近 2 ステップ）と `docs/tasks.md`（Done セクション）を読み、
   前回のドキュメント更新以降の変更点を把握する。

2. `docs/tasks.md` に「ドキュメント更新」タスクを In Progress として追加する（CLAUDE.md のルール）。

3. 以下の **3エージェントを同一メッセージで同時起動** する（順次起動では効果が半減する）:

   **Agent 1 — README.md**
   - 参照: `src/presentation/routers/*.py`, `src/presentation/schemas.py`, `frontend/src/pages/`
   - 更新対象: API リファレンス、HITL フロー、プロジェクト構成
   - 作業: Read → 変更を特定 → Write で全文上書き

   **Agent 2 — docs/architecture.md**
   - 参照: `src/infrastructure/*agent*.py`, `src/infrastructure/db/models.py`, `alembic/versions/`, `frontend/src/pages/`
   - 更新対象: エージェント構成図、DB スキーマ、ツール一覧、フロントエンド画面一覧
   - 作業: Read → 変更を特定 → Write で全文上書き

   **Agent 3 — docs/requirements.md**
   - 参照: `docs/tasks.md`（Done セクション）, `docs/progress.md`
   - 更新対象: Functional Requirements（新完了機能を実装済みに移動、状態を Done に変更）
   - 作業: Read → 変更を特定 → Write で全文上書き

4. 3エージェントの完了を確認後、`git add` してコミット:
   ```
   docs: update README/architecture/requirements for <フェーズ名>
   ```

5. CLAUDE.md の End-of-step チェックリストを実行:
   - `docs/tasks.md`: In Progress → Done
   - `docs/progress.md`: Current Status 更新 + Step ログ追記
