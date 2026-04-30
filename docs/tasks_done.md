# Done Tasks — Archive

完了タスクのアーカイブ。新規タスクの追加・参照は `docs/tasks.md` を使用すること。

---

- Phase 38: agent.py 要否確認 — fo_agent/bo_agent 実装後も旧 /api/v1/triage エンドポイント（router.py + triage_use_case.py + frontend/src/api/triage.ts）が現役のため削除不可と判定。削除には旧エンドポイント廃止を伴う別タスクが必要
- Phase 37: ドキュメント最新化 + CLAUDE.md 自動更新ルール追加 — tasks/requirements/architecture を Phase 35 相当に最新化、tasks_done.md 新設、CLAUDE.md の End-of-step checklist に architecture.md/requirements.md 更新ルール追記
- Phase 35: LLM コスト集計機能 — LlmCostLogModel + Alembic 0006 migration、llm_cost_log_repository（save_batch/get_summary/get_daily_costs）、TriageResult に cost_log/total_cost_usd 追加、FO/BO use case からコスト保存、GET /api/v1/cost/summary + GET /api/v1/cost/logs、CostPage（サマリーカード・エージェント別・モデル別・日次テーブル・最近の呼び出しログ）、NavBar "Cost" リンク追加、version 0.5.0 → 0.6.0
- Phase 34: Rule一覧画面 — GET /api/v1/rules エンドポイント追加（FO 9ルール・BO 8ルールのメタデータ返却）、RuleListPage.tsx 新規作成（FO/BO 別テーブル、severity バッジ・stub フラグ表示）、NavBar に "Rules" リンク追加、version 0.4.0 → 0.5.0
- Phase 33: seed / rule_engine 整合性修正 — FO_RULES に counterparty_exists・instrument_exists stub 追加、BO_RULES に settlement_confirmed stub 追加、seed.py を静的チェック結果 pre-seed 方式に再設計（TRD-004/005 を FoAgentToCheck + fo_check_results、TRD-001〜003/008〜013 を BoAgentToCheck + fo/bo_check_results 付きで登録、_wf_status バグ修正）、Zenith Trading Corp（非アクティブ CP）の USD SSI をマスタに追加（TRD-009 が counterparty_active のみ失敗し AG01 パスになるよう調整）
- Phase 32: ハイブリッドエージェント デモ準備 — test_determine_triage_path.py（24テスト）、test_gather_context_routing.py（11テスト）、test_hybrid_routing.py（9テスト、全102件通過）、TRD-013 を mock_store.py + seed.py に追加（AM04 シナリオ、workflow_status=BoAgentToCheck + bo_check_results プリシード）、docs/demo_hybrid_agent.md（8シナリオのcurlデモ手順書）
- Phase 31: BO/FO エージェント ハイブリッド構造リファクタリング — gather_context_node（決定論的データ収集）、AG01/BE01/AM04/MISSING_SSI 別ハンドラノード、HITL ノード二重登録（決定論的パス用 + deep_investigation 用）、_determine_triage_path 純粋関数、BO_SYSTEM_PROMPT / FO_SYSTEM_PROMPT から INVESTIGATION STEPS 削除（~40 行削減）、bo_triage_use_case.py の _BO_ALL_HITL_NODE_NAMES 対応 + resume() as_node 修正
- Phase 30: コスト計測・モデル選択機能 — utils/cost_tracker.py（価格テーブル/calc_cost/build_cost_log/select_model/call_with_cost_tracking）、FoAgentState/BoAgentState に cost_log・total_cost_usd・task_type・selected_model 追加、model_router_node を fo/bo_agent 先頭に挿入（task_type と $0.10 閾値でモデル選択 + 監査ログ）、agent_node を call_with_cost_tracking() でラップ、use_case initial_state 更新、test_cost_tracker.py 追加（24テスト、計58件通過）
- Phase 29: stp_status カラム削除 — TradeStatus enum 削除、models.py/trade_repository.py/seed.py/schemas.py/trades.py/stp_exceptions.py から stp_status 参照を全削除、alembic/versions/0005_drop_stp_status.py 追加、フロントエンド（types/api/TradeListPage/TradeDetailPage）から stp_status フィルタ・列・表示を削除、frontend version 0.2.1 → 0.3.0
- Phase 27: 取引入力機能 + maybe_run_fo_check チェーン修正 — TradeCreateRequest スキーマ追加、POST /api/v1/trades エンドポイント追加、maybe_run_fo_check が FoValidated 時に maybe_run_bo_check を自動チェーン、fo-check エンドポイントも同様に修正、TradeInputPage（日付カレンダー + マスタデータ選択）、TradeListPage に "New Trade" ボタン、フロントエンドバージョン 0.1.8 → 0.2.0
- Phase 26-F: フロントエンド — TradeOut に check results 追加、TradeDetailPage（4タブ: FoCheck/BoCheck/Events/Triage）、SettingsPage、TradeListPage 更新（workflow_status列/フィルタ/クリックナビ）、NavBar+App.tsx 更新
- Phase 26-E: トレードイベント API — schemas.py に TradeVersionOut/TradeEventOut/TradeEventListResponse/TradeEventCreateRequest/EventApproveRequest 追加、routers/trade_events.py（GET list / POST create / PATCH fo-approve / PATCH bo-approve、状態機械: FoUserToValidate→FoValidated→Done、AMEND承認で activate_version()+Initial 遷移、CANCEL承認で Cancelled 遷移）
- Phase 26-D: FoAgent 新規実装 — tools.py に get_fo_check_results/get_bo_sendback_reason/create_amend_event/create_cancel_event/provide_explanation/escalate_to_fo_user 追加 + FO_*_TOOLS エクスポート、fo_agent.py（FoAgentState + build_fo_graph() + 2 HITL ノード + FO_SYSTEM_PROMPT）、fo_triage_use_case.py（FoTriageUseCase）、routers/fo_triage.py（POST /api/v1/trades/{id}/fo-triage + resume）
- Phase 26-C: BoAgent リネーム + 拡張 — tools.py に get_bo_check_results/get_fo_explanation/send_back_to_fo/escalate_to_bo_user 追加、bo_agent.py（BoAgentState + build_bo_graph() + 4 HITL ノード + BO_SYSTEM_PROMPT）、bo_triage_use_case.py（BoTriageUseCase）、routers/bo_triage.py（POST /api/v1/trades/{id}/bo-triage + resume）、test_entities.py の RootCause 期待値更新
- Phase 26-B: ルールエンジン — CheckResult に severity 追加、check_rules.py（FoRule/BoRule + FoCheck 9 ルール + BoCheck 8 ルール）、rule_engine.py（run_fo_check/run_bo_check/maybe_* auto-trigger）、POST /api/v1/trades/{id}/fo-check・bo-check エンドポイント、settings.py ルーター（GET /api/v1/settings + PATCH /api/v1/settings/{key}）
- Phase 26-A: DB Foundation — TradeWorkflowStatus/EventType/CheckResult エンティティ追加、TradeModel PK→UUID + version/workflow_status/is_current 等カラム追加、TradeEventModel/AppSettingModel 新規、Alembic 0003 マイグレーション、seed.py 更新（workflow_status, app_settings）、trade_repository.py 拡張、trade_event_repository.py / app_setting_repository.py 新規
- Phase 25: アクセス制御 — Nginx Basic Auth（フロント）+ API キー（バックエンド LLM エンドポイント）
- Phase 24-D: パターン分析 — システムプロンプトに get_counterparty_exception_history（30日3件超で警告）、get_triage_history（解決済み事例の反映）調査手順を追加
- Phase 24-C: アクション多様化（HITL 拡張）— TriagePage.tsx の HitlPanel コンポーネントに register_ssi / reactivate_counterparty / update_ssi / escalate 各アクション用 UI 追加、Backend に pending_action_type フィールド追加
- Phase 24-B: 複雑・曖昧なシナリオ追加 — TRD-008〜012 追加（AC01/AG01/COMPOUND/IBAN_FORMAT_ERROR/UNKNOWN）、システムプロンプトに SWIFT コード知識追加
- Phase 24-A: ツール追加 — get_triage_history/get_counterparty_exception_history/reactivate_counterparty/update_ssi/escalate を tools.py + agent.py + triage_use_case.py に追加、HITL 汎化（_HITL_TOOL_TO_NODE + _make_hitl_node）
- Phase 22 前半: VM への自動デプロイ — GitHub Actions + SSH、environment: GCP_VM、concurrency で多重実行防止
- Phase 20: バックエンドを Cloud Run に移行 — entrypoint.sh、Artifact Registry、2ジョブ workflow（Cloud Run + VM SSH）
- Phase 19: DB を Neon PostgreSQL に移行 — postgres コンテナ削除、DATABASE_URL を外部化
- Phase 17+18: Frontend routing + all CRUD pages — NavBar, PageLayout, Pagination, TradeListPage, CounterpartyListPage/EditPage, StpExceptionListPage/CreatePage, theme.ts
- Phase 16: LangGraph tools DB migration — tools.py DB/mock fallback、ssi_repository、reference_data_repository
- Phase 15: Backend CRUD API — trade/counterparty/stp_exception repositories + routers、schemas、CORS fix
- Phase 14: DB Foundation + Seed — 5 ORM models、Alembic 0002 migration、seed.py、TradeStatus/StpExceptionStatus entities
- Phase 11: React Frontend — frontend/ (Vite + React 18 + TypeScript, TriagePage, HITL UI)
- Phase 10: Secret Manager 抽象化レイヤー — secrets.py、SECRET_BACKEND 環境変数で .env / GCP 切り替え
- Phase 9: PostgreSQL DB layer + Alembic — SQLAlchemy ORM、alembic.ini、0001 migration、repository、history endpoint
- Phase 8: Containerization — Dockerfile (multi-stage)、.dockerignore、docker-compose.yml (+test service)
- Phase 7: Documentation — README.md、docs/architecture.md
- Phase 6: Observability — logging_config.py、構造化 JSON ロギング（agent + use_case）
- Phase 5: Testing — unit tests × 3 files、integration tests × 6 cases
- Phase 4: Presentation layer — schemas.py、router.py、main.py
- Phase 3: Infrastructure layer — mock_store.py、tools.py、agent.py、triage_use_case.py
- Phase 2: Domain layer — entities.py、interfaces.py
- Phase 1: Project scaffolding — pyproject.toml、src/ structure、.env.example、tests/
- Process improvement: CLAUDE.md task state transitions、tasks.md/progress.md restructure
- Development rules setup (CLAUDE.md、progress.md、requirements.md、tasks.md)
- Use case definition: STP Exception Triage Agent
