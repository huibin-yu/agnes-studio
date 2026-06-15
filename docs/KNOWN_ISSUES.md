# Known Issues

## 视频生成阶段失败不自动退款（截至 Stage 2）

**现象**：用户调用 `/api/videos/generate` 后，若 Agnes 上游已成功创建任务（已扣积分），
但后续 poll 拿到 `status=failed`，当前积分**不会自动退还**。

**临时缓解**：用户可联系运营手工调账。

**根治计划**：Stage 3（积分 ledger）上线后通过补偿脚本统一退款，并在 `poll_video_status`
看到 `status=failed` 时实时退款。

## 新增列后需手工 ALTER（生产 SQLite/PG）

`Base.metadata.create_all` 不会为已存在的表新增列。Stage 2 / Stage 3 引入新列时：

```sql
-- Stage 2
ALTER TABLE video_generations ADD COLUMN credits_charged INTEGER DEFAULT 0 NOT NULL;

-- Stage 3 创建新表（create_all 会自动建，无需手工）
```

测试用 SQLite in-memory，每次重建，不受影响。
