# fastapi-vue-admin-scaffold

FastAPI + Vue 3 **管理端脚手架**（非成品业务系统）。包含登录、动态菜单，以及用户、角色、菜单权限、操作日志、可配置定时任务。界面组件使用 Ant Design Vue。

## 本地启动

需要 uv 和 Node.js 20 以上。

```powershell
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 。种子账号 `admin`，密码 `admin123`。

启动时会在 `backend/dev.db` 建表并写入种子数据。JWT 密钥请在 `backend/.env` 里修改，可以先复制 `.env.example`。

### 定时任务

定时任务与 API **同一进程**运行（APScheduler），随 `uvicorn` / Docker 里的 `api` 服务一起启停。在后台 **系统管理 → 定时任务** 中可查看、编辑触发规则、启停、手动执行并查看执行日志。执行日志支持全部清理、清理 7 天前、清理 30 天前（1 个月），清理前会显示各档的条数。

首次启动会自动写入内置任务（清理过期登录锁定、清理操作日志等）。新增可调度逻辑：在 `backend/app/jobs/tasks.py` 用 `@job` 注册处理器，保存任务后调度器会从数据库热更新。

环境变量（`backend/.env` 或 Docker 根目录 `.env`）：

```text
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Shanghai
OPERATION_LOG_RETENTION_DAYS=180
```

`OPERATION_LOG_RETENTION_DAYS=0` 时不会创建「清理操作日志」内置任务。请保持 API **单 worker**；多 worker 时每个进程都会调度，应设 `SCHEDULER_ENABLED=false`。

### 谷歌验证器（TOTP）

按**单个用户**配置，在 **系统管理 → 用户管理** 中编辑用户，用「谷歌验证」开关启用或关闭。

- **关闭**：该用户登录只需用户名密码。
- **启用 + 待绑定**：账号密码验证通过后，在**登录页**展示二维码并完成绑定，成功后才进入后台。
- **启用 + 已绑定**：账号密码验证通过后，须在**登录页**输入 6 位谷歌验证码才能进入后台。
- **重置验证器**（用户列表操作）：保留「启用」策略，仅清除绑定，用户需重新绑定。
- **重置密码**会同时清除验证器绑定；在编辑里关闭「谷歌验证」也会清除绑定。

## 测试

```powershell
cd backend
uv run pytest
```

## 数据表命名

系统内置表统一使用 `sys_` 前缀：`sys_users`、`sys_roles`、`sys_menus`、`sys_user_roles`、`sys_role_menus`、`sys_operation_logs`、`sys_scheduled_jobs`、`sys_scheduled_job_logs`。

所有时间字段统一存 **13 位毫秒时间戳**（`BIGINT`，epoch milliseconds），接口直接返回数字，前端用 `src/utils/time.ts` 的 `formatDateTime` 显示。旧版本用 `DATETIME` 建的库不兼容，删除 `backend/dev.db`（或重建 Postgres 库）后重启即可，脚手架不迁移历史数据。

旧版本建的库（没有前缀）在首次启动时会自动原地重命名，数据保留；使用 Alembic 的库执行 `uv run alembic upgrade head`（迁移 `20261031_0006`）即可。

## 目录

- `backend/app/api`：路由
- `backend/app/services`：业务规则
- `backend/app/models`：表结构（系统表均为 `sys_` 前缀）
- `frontend/src/views`：页面。菜单里的组件字段对应这里的路径，例如 `system/user/index`
- `frontend/src/router`：登录后按菜单注册路由
- `skills/admin-frontend`：管理端前端 Agent 规范（Ant Design Vue 列表/弹窗/权限等），安装方式见 `skills/README.md`

## Docker 部署

需要安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（或可用的 Docker Engine + Compose）。

在项目根目录执行：

```powershell
copy .env.docker.example .env
docker compose up -d --build
```

浏览器打开 http://localhost:8080（端口可在 `.env` 里用 `WEB_PORT` 修改）。种子账号仍是 `admin` / `admin123`。

Compose 会构建并启动三个逻辑组件：

| 服务 | 说明 |
| --- | --- |
| `web` | Nginx 托管前端，`/api` 反代到后端 |
| `api` | FastAPI，启动时建表、种子数据，并运行内置定时任务 |
| `postgres` | 仅在使用 PostgreSQL 配置时启动（见下） |

上线前请在 `.env` 中修改 `JWT_SECRET`（至少 32 字符）和数据库密码（若用 PostgreSQL）。

### 数据库：SQLite（默认）

不额外配置时，使用 SQLite，库文件路径为容器内 `/data/app.db`，数据保存在 Docker 卷 `appdata` 中：

```text
DATABASE_URL=sqlite:////data/app.db
```

适合单机、轻量部署，与本地 `backend/dev.db` 一样是 SQLite，只是运行在容器里并持久化到卷。

### 数据库：PostgreSQL

在 `.env` 中启用 `postgres` profile，并改用 PostgreSQL 连接串（同时注释掉 SQLite 的 `DATABASE_URL`）：

```text
COMPOSE_PROFILES=postgres
DATABASE_URL=postgresql+psycopg://python_admin:python_admin@postgres:5432/python_admin
POSTGRES_USER=python_admin
POSTGRES_PASSWORD=python_admin
POSTGRES_DB=python_admin
```

然后同样执行 `docker compose up -d --build`。Postgres 数据在卷 `pgdata` 中。

### 常用命令

```powershell
docker compose ps
docker compose logs -f api
docker compose down
docker compose down -v
```

`down -v` 会删除 `appdata` / `pgdata` 卷，数据库数据一并清空，慎用。

### 环境变量说明

根目录 `.env` 由 `.env.docker.example` 复制而来，主要项：

- `JWT_SECRET`：JWT 签名密钥
- `WEB_PORT`：对外访问端口，默认 `8080`
- `CORS_ORIGINS`：需与浏览器访问地址一致，默认 `http://localhost:8080`
- `DATABASE_URL`：数据库连接（SQLite 或 PostgreSQL）
- `SEED_ON_STARTUP` / `AUTO_CREATE_TABLES`：首次启动建表与种子数据，一般保持 `true`
- `SCHEDULER_ENABLED` / `SCHEDULER_TIMEZONE` / `OPERATION_LOG_RETENTION_DAYS`：见上文「定时任务」

本地开发时的后端配置仍使用 `backend/.env`（见 `.env.example`），与 Docker 用的根目录 `.env` 相互独立。

## 本地开发使用 PostgreSQL

若只在本地用 uv 跑后端，但数据库想用 Postgres，可以只启动数据库容器：

```powershell
docker compose --profile postgres up -d postgres
```

在 `backend/.env` 中配置：

```text
DATABASE_URL=postgresql+psycopg://python_admin:python_admin@localhost:5432/python_admin
AUTO_CREATE_TABLES=true
```

也可以在空库上执行 `uv run alembic upgrade head`，这时把 `AUTO_CREATE_TABLES` 设为 `false`。不要对已经由启动过程建好的库再执行同一份初始迁移。

## 加一个业务页面

1. 在 `frontend/src/views` 下加页面。
2. 在菜单管理里新增页面，组件字段写成相对 `views` 的路径，不含 `.vue`。
3. 按钮权限用 `v-permission="'模块:资源:动作'"`，后端接口用同样的标识做校验。
