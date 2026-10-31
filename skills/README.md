# Agent Skills

本目录随脚手架一起分发，供 Cursor 等 Agent 在改管理端前端时遵循同一套 UI/交互规范。

## admin-frontend

Vue 3 + Ant Design Vue 后台页面规范（列表铺满、表格自适应、状态开关、菜单类型三色标签、双列弹窗、`v-permission`、中文文案等）。详见 [admin-frontend/SKILL.md](./admin-frontend/SKILL.md)。

### 在 Cursor 里启用

任选其一：

1. **复制到用户 Skills 目录**（推荐，全局可用）  
   将 `skills/admin-frontend` 整个文件夹复制到：

   - Windows：`%USERPROFILE%\.cursor\skills\admin-frontend`
   - macOS / Linux：`~/.cursor/skills/admin-frontend`

2. **仅当前项目**  
   复制到项目下的 `.cursor/skills/admin-frontend`（若目录不存在请先创建）。

复制后重启 Cursor 或新开 Agent 对话，Agent 即可按 skill 描述自动选用该规范。
