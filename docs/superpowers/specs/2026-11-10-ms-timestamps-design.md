# 时间字段改为 13 位毫秒时间戳设计

日期：2026-11-10
状态：已确认（2026-11-10）

## 意图

数据库所有时间列改为存 13 位毫秒时间戳（epoch ms 的整数），不使用 `DATETIME`/`TIMESTAMP`；接口也直接返回这个整数，前端统一格式化显示。

## 范围

**数据库列（8 个）**

| 表 | 列 |
| --- | --- |
| `sys_users` | `locked_until`、`created_at`、`updated_at` |
| `sys_operation_logs` | `created_at` |
| `sys_scheduled_jobs` | `last_run_at`、`created_at`、`updated_at` |
| `sys_scheduled_job_logs` | `started_at`、`finished_at` |

实际是 9 个：`locked_until`、`created_at`×3、`updated_at`×2、`last_run_at`、`started_at`、`finished_at`。

**接口字段**：`users.created_at`、`operation_logs.created_at`、`scheduled_jobs.last_run_at/created_at/updated_at`、`scheduled_job_logs.started_at/finished_at` 全部返回整数。

**前端**：操作日志列表/详情、定时任务「上次执行」、执行日志「开始时间/结束时间」改为格式化显示。

## 非目标

- JWT 的 `iat`/`exp` 仍按 RFC 用秒，不属数据库时间。
- 不改变时区语义：显示仍按浏览器本地时区。
- 不改分页、筛选、权限。

## 方案

- **存储**：`BigInteger`，值 = `time.time_ns() // 1_000_000`。
- **写入/比较**：新增 `app/core/time.py` 的 `now_ms()`；锁定、清理任务、保留天数全部用整数比较。
- **读取**：服务层直接把 ms 放进响应，不再 `strftime` / `isoformat`。
- **前端**：新增 `src/utils/time.ts` 的 `formatDateTime(ms)`，本地时区输出 `YYYY-MM-DD HH:mm:ss`，空值 `—`。

### 旧库迁移（已选 B）

用户确认：这只是脚手架，不处理历史数据，默认数据正确即可。

- 模型、接口、前端全部改为毫秒；Alembic 初始链（0001/0002/0003/0005）直接改成 `BIGINT`，新库 `alembic upgrade head` 即可。
- 旧库（`DATETIME` 列）不做迁移：删除 `backend/dev.db` 或重建 Postgres 库后启动，会按新模型建表并写入种子数据。

## 细节

- `ensure_user_columns` 里补 `locked_until` 的 SQL 类型同步改成 `BIGINT`。
- 登录锁定：`locked_until > now_ms()`；写 `now_ms() + 分钟*60_000`。
- 清理任务：`created_at < now_ms() - days*86_400_000`。
- 调度器：`started`/`finished`/`last_run_at`/`updated_at` 全部 ms。
- 操作日志中间件不受影响（`created_at` 由模型默认值写）。
- 前端类型定义由 `string` 改为 `number`；表格列用 `bodyCell` 格式化，详情用 `formatDateTime`。
- 空值统一 `—`，与现有 UI 一致。

## 验收

- 新库建表后，所有时间列是 `BIGINT`（SQLite 为 INTEGER），值是 13 位数字。
- 旧库（含数据）启动后自动转换，数据条数不变，时间显示与转换前一致。
- 所有相关接口返回数字；页面显示格式不变。
- `uv run pytest`、`npm run build`、前端 formatter 单测通过。
