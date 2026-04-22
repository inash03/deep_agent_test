# Skills

このファイルはプロジェクト固有の繰り返し手順（スキル）を定義する。
`CLAUDE.md` のルールと併用すること。

---

## update-docs — ドキュメント一括更新

**対象ファイル:** `README.md` / `docs/architecture.md` / `docs/requirements.md`

### 問題

3ファイルを1つのレスポンスで更新しようとすると、LLM のストリーミング中に
無通信時間が生まれ **"API Error: Stream idle timeout - partial response received"** が発生する。

### 解決策

`Agent` ツールで各ファイルを **独立したサブエージェントに並列委譲** する。
各エージェントが1ファイルのみを担当するため個々の応答が短くなり、タイムアウトを防げる。

### 実行手順

1. `docs/progress.md`（直近 2 ステップ）と `docs/tasks.md`（Done セクション）を読み、
   前回のドキュメント更新以降の変更点を把握する。

2. 以下の **3エージェントを同一メッセージで同時起動** する（順次起動では効果が半減する）:

   | エージェント | 担当ファイル | 参照すべきソース |
   |---|---|---|
   | Agent 1 | `README.md` | `src/presentation/routers/*.py`, `src/presentation/schemas.py` |
   | Agent 2 | `docs/architecture.md` | `src/infrastructure/*agent*.py`, `src/infrastructure/db/models.py`, `alembic/versions/` |
   | Agent 3 | `docs/requirements.md` | `docs/tasks.md`（Done セクション）, `docs/progress.md` |

3. 各エージェントへの指示に必ず含める情報:
   - 対象ファイルの絶対パス
   - 追加・変更すべき内容の箇条書き（具体的に）
   - 参照ファイルの絶対パス
   - 「現在のファイルを Read で読んでから Write ツールで完全な新内容を書き出すこと」

4. 全エージェント完了後に変更内容をレビューしてコミットする。

### 各エージェント指示のテンプレート

#### README.md エージェント

```
/home/user/deep_agent_test/README.md を最新コードに合わせて更新してください。

【作業】
1. Read ツールで現在の README.md を読む
2. 下記の変更を反映した完全な新内容を Write ツールで書き出す

【変更点】
- (変更箇条書きをここに列挙)

【参照ファイル】
- /home/user/deep_agent_test/src/presentation/routers/ 配下の各ルーターファイル
- /home/user/deep_agent_test/src/presentation/schemas.py
- /home/user/deep_agent_test/frontend/src/pages/ 配下のページファイル一覧
```

#### docs/architecture.md エージェント

```
/home/user/deep_agent_test/docs/architecture.md を最新コードに合わせて更新してください。

【作業】
1. Read ツールで現在の architecture.md を読む
2. 下記の変更を反映した完全な新内容を Write ツールで書き出す

【変更点】
- (変更箇条書きをここに列挙)

【参照ファイル】
- /home/user/deep_agent_test/src/infrastructure/fo_agent.py
- /home/user/deep_agent_test/src/infrastructure/bo_agent.py
- /home/user/deep_agent_test/src/infrastructure/db/models.py
- /home/user/deep_agent_test/alembic/versions/ 配下のマイグレーションファイル
- /home/user/deep_agent_test/frontend/src/pages/ 配下のページファイル一覧
```

#### docs/requirements.md エージェント

```
/home/user/deep_agent_test/docs/requirements.md を最新コードに合わせて更新してください。

【作業】
1. Read ツールで現在の requirements.md を読む
2. 下記の変更を反映した完全な新内容を Write ツールで書き出す

【変更点】
- (変更箇条書きをここに列挙)

【参照ファイル】
- /home/user/deep_agent_test/docs/tasks.md（Done セクション）
- /home/user/deep_agent_test/docs/progress.md（直近のステップ）
```

### 注意事項

- **同時起動が必須**: `Agent` ツールの呼び出しは1メッセージにまとめること。
- **参照ファイルを明示**: 各エージェントは会話コンテキストを持たないため、
  必要なファイルのパスをプロンプトに明記する。
- **タスク管理**: このスキル実行も `docs/tasks.md` にタスクとして記録し、
  完了後に Done に移動する。

---

## （スキルを追加する場合はここに続ける）
