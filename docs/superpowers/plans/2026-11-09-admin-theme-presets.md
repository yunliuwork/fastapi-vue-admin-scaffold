# 管理端多配色（个人切换）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给管理端加入 4 套可切换配色，选择存浏览器，点一下全站即时生效。

**Architecture:** 一套 palette 对象同时生成 `<html>` 上的 CSS 变量和 Ant Design `ThemeConfig`，颜色只有一个来源；Pinia store 负责持久化与切换，顶栏 popover 提供入口。

**Tech Stack:** Vue 3、Pinia、ant-design-vue 4、Vite；无新增依赖。

**Spec:** `docs/superpowers/specs/2026-11-09-admin-theme-presets-design.md`

## Global Constraints

- 不新增 npm 依赖。
- 所有主题色来自 `src/theme/presets.ts`；组件里不得写死主题色。
- 语义色固定：成功 `#0E7C74`、失败 `#A33B32`；菜单三色标签（目录 `#1B5FC1`、页面 `#0B6B64`、按钮 `#A85A00`）不随主题变。
- 持久化 key：`admin:theme`；默认 `celadon`（青瓷）。
- 侧栏宽度/折叠/手风琴/表格自适应行为不变。
- 每个任务结束 `cd frontend && npm run build` 必须通过。
- 本地端口：后端 8000，前端 5174。

## Review Focus

- 刷新时首屏是否会先看到默认色：变量必须在 `app.mount()` 之前写好，且 `body` 背景用的是 `--paper`。
- `localStorage` 里是拼错/旧版本的 id：必须回退到青瓷，不能出现空变量。
- 静态 `Modal.confirm` 的主按钮是否跟随主题（它可能不在 `ConfigProvider` 树里）——切到海蓝后打开「停用角色」确认框验证。
- 深色侧栏上新主题文字（`--menu-text`）的对比度是否够。
- 登录页背景光晕在非青瓷主题下的偏色是否过火（`hue-rotate` 的值）。

---

### Task 0: 提交既有改动与文档

**Files:**
- Modify: `docs/superpowers/specs/2026-11-09-admin-theme-presets-design.md`（状态改为「已确认」）
- Commit: 现有 `frontend/src/layouts/AdminLayout.vue`（侧栏手风琴）、`skills/admin-frontend/SKILL.md`（手风琴说明）

- [ ] **Step 1: 改设计文档状态**

把文件头部的 `状态：待确认` 改成 `状态：已确认（2026-11-09）`。

- [ ] **Step 2: 提交文档**

```bash
git add docs/superpowers
git commit -m "docs: 管理端多配色设计文档与实施计划"
```

- [ ] **Step 3: 提交手风琴与 skill**

```bash
git add frontend/src/layouts/AdminLayout.vue skills/admin-frontend/SKILL.md
git commit -m "feat: 侧栏菜单改为手风琴"
```

---

### Task 1: 配色 preset 与 AntD 主题构造器

**Files:**
- Create: `frontend/src/theme/presets.ts`
- Modify: `frontend/src/theme.ts`

**Interfaces:**
- Produces:
  - `interface ThemePalette { id: string; label: string; accent: string; ink: string; menuSub: string; menuHover: string; menuText: string; paper: string; sheet: string; line: string; text: string; muted: string; rowAlt: string; rowHover: string; headerBg: string; accentSoft: string; accountHover: string; loginHue: string }`
  - `const palettes: ThemePalette[]`（顺序：celadon、ocean、violet、ochre）
  - `const DEFAULT_PALETTE_ID = 'celadon'`
  - `function getPalette(id: string): ThemePalette`（找不到时返回默认）
  - `function buildAntdTheme(palette: ThemePalette): ThemeConfig`（在 `theme.ts`，替换原来的静态 `theme`）

- [ ] **Step 1: 写 `presets.ts`**

按 spec 的表把 4 套颜色写成 `palettes`；`label` 依次为「青瓷 / 海蓝 / 墨紫 / 赭石」。`getPalette` 用 `palettes.find(...) ?? palettes[0]`。

- [ ] **Step 2: 改 `theme.ts`**

保留 `borderRadius`、`fontFamily`、`controlHeight` 等基础 token；把 `colorPrimary`、`colorInfo`、`colorLink`、`colorBgLayout`、`colorText`、`colorTextSecondary`、`colorBorder`、`Menu.*`、`Layout.*` 全部改成从 `palette` 取值。导出 `buildAntdTheme`，并临时保留 `export const theme = buildAntdTheme(palettes[0])`（Task 2 切到 store 后再删）。

- [ ] **Step 3: 构建**

Run: `cd frontend && npm run build`
Expected: `✓ built`，无 `error TS`

- [ ] **Step 4: 提交**

```bash
git add frontend/src/theme.ts frontend/src/theme/presets.ts
git commit -m "feat: 增加四套主题配色 preset"
```

---

### Task 2: 主题 store 与启动时应用

**Files:**
- Create: `frontend/src/stores/theme.ts`
- Modify: `frontend/src/main.ts`、`frontend/src/App.vue`

**Interfaces:**
- Consumes: `palettes`、`DEFAULT_PALETTE_ID`、`getPalette`、`buildAntdTheme`
- Produces: `useThemeStore()`，state `paletteId: string`；getters `palette: ThemePalette`、`themeConfig: ThemeConfig`；actions `setPalette(id: string): void`、`apply(): void`（apply 同时同步 `ConfigProvider.config`）

- [ ] **Step 1: 写 store**

```ts
const STORAGE_KEY = 'admin:theme'
// state 初始化：读 localStorage，try/catch，无效 id 回退 DEFAULT_PALETTE_ID
// apply(): 把 palette 的字段转成 --kebab-case 变量 setProperty 到 document.documentElement，
//          并 setAttribute('data-theme', paletteId)
//          再调用 ConfigProvider.config({ theme: buildAntdTheme(palette), autoInsertSpaceInButton: false })，
//          让静态 Modal.confirm 也跟随主题（它不继承组件树里的 ConfigProvider）
// setPalette(id): getPalette(id) -> state -> localStorage.setItem -> apply()
```

变量名映射：`menuSub → --menu-sub`、`rowAlt → --row-alt`、`headerBg → --header-bg`、`accentSoft → --accent-soft`、`accountHover → --account-hover`、`loginHue → --login-hue`，其余同名。

- [ ] **Step 2: 启动前应用**

`main.ts`：`app.use(createPinia())` 之后、`app.mount('#app')` 之前调用 `useThemeStore().apply()`。

- [ ] **Step 3: App.vue 用 store**

`const themeStore = useThemeStore()`，`<ConfigProvider :theme="themeStore.themeConfig" …>`；删除对 `./theme` 的 `theme` 引用。随后删除 `theme.ts` 里临时的 `export const theme`。

- [ ] **Step 4: 构建**

Run: `cd frontend && npm run build`
Expected: 通过

- [ ] **Step 5: 验证持久化与回退**

启动前后端（8000/5174）后，在浏览器控制台：

```js
localStorage.setItem('admin:theme', 'ocean'); location.reload()
```

Expected: 重新加载后 `getComputedStyle(document.documentElement).getPropertyValue('--accent')` 为 `#2563C9`，主按钮背景为海蓝；把值改成 `nope` 再刷新，回到青瓷，不报错。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/stores/theme.ts frontend/src/main.ts frontend/src/App.vue frontend/src/theme.ts
git commit -m "feat: 主题 store 与启动时应用配色"
```

---

### Task 3: CSS 变量化清扫

**Files:**
- Modify: `frontend/src/styles/global.css`、`frontend/src/layouts/AdminLayout.vue`、`frontend/src/views/dashboard/index.vue`、`frontend/src/views/system/log/index.vue`、`frontend/src/views/login/index.vue`

**Interfaces:**
- Consumes: Task 2 写入的 CSS 变量（`--accent`、`--ink`、`--menu-sub`、`--menu-hover`、`--menu-text`、`--paper`、`--sheet`、`--line`、`--text`、`--muted`、`--row-alt`、`--row-hover`、`--header-bg`、`--accent-soft`、`--account-hover`、`--login-hue`）

- [ ] **Step 1: 补默认变量**

`global.css` 的 `:root` 保留现有变量值（青瓷，作为无 JS 时的兜底），新增 `--menu-sub: #102628`、`--menu-hover: #1d4548`、`--menu-text: #d7e4e2`、`--header-bg: #f7faf9`、`--accent-soft: #eef6f5`、`--account-hover: #e7eeed`、`--login-hue: 0deg`。

- [ ] **Step 2: 替换写死颜色**

- `global.css`：表头 `#f7faf9` → `var(--header-bg)`。
- `AdminLayout.vue`：`:style="{ background: '#163033' }"` → `var(--ink)`；`.brand` 颜色 `#f4f7f6` → `var(--menu-text)`；`.header` 背景 `#f7faf9` → `var(--header-bg)`；`.account:hover` 背景 `#e7eeed` → `var(--account-hover)`。
- `dashboard/index.vue`：`.stats .focus` `#eef6f5` → `var(--accent-soft)`；表格表头 `#f7faf9` → `var(--header-bg)`；`.mark` `#eef2f1` → `var(--row-alt)`；`.mark[data-hot]` `#e4f2f0` → `var(--accent-soft)`。
- `log/index.vue`：`dt` 的 `#5c6b69` → `var(--muted)`；`pre` 的 `#f7faf9` → `var(--header-bg)`。
- 语义色 `#0e7c74`/`#a33b32`、类型标签色保持不动。

- [ ] **Step 3: 登录页背景偏色**

`login/index.vue`：`.login` 保持 `background-color: var(--ink)`，把背景图移到 `::before`（`position:absolute; inset:0; background: url(...) center/cover no-repeat; filter: hue-rotate(var(--login-hue));`），`.login` 加 `position: relative; overflow: hidden`，卡片等内容加 `position: relative; z-index: 1`。

- [ ] **Step 4: 构建**

Run: `cd frontend && npm run build`
Expected: 通过

- [ ] **Step 5: 视觉检查**

窗口 1440×900，依次设置 `admin:theme` 为 celadon/ocean/violet/ochre 刷新：侧栏、菜单选中、顶栏、表格斑马纹、工作台浅色块都随主题变；登录页光晕偏色自然；侧栏文字可读。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/styles/global.css frontend/src/layouts/AdminLayout.vue frontend/src/views/dashboard/index.vue frontend/src/views/system/log/index.vue frontend/src/views/login/index.vue
git commit -m "style: 主题色改为 CSS 变量驱动"
```

---

### Task 4: 顶栏配色切换器

**Files:**
- Modify: `frontend/src/layouts/AdminLayout.vue`

**Interfaces:**
- Consumes: `useThemeStore`（Task 2）、`palettes`（Task 1）

- [ ] **Step 1: 加入 popover**

顶栏右侧（用户下拉左侧）加 `a-popover`：触发器是 `a-button type="text" aria-label="切换配色"` + `BgColorsOutlined`；内容为四行按钮，每行三色圆点（`ink`/`paper`/`accent`）+ 名称 + 当前项 `CheckOutlined`；点击行调用 `themeStore.setPalette(p.id)`。popover 的 `trigger="click"`、`placement="bottomRight"`。

- [ ] **Step 2: 样式**

`.theme-row` 用 `display:flex; align-items:center; gap:10px; width:100%; padding:8px 10px; border:0; border-radius:6px; background:transparent; cursor:pointer;`；hover 用 `var(--account-hover)`；active 项文字加粗。圆点 10px 圆形。

- [ ] **Step 3: 构建**

Run: `cd frontend && npm run build`
Expected: 通过

- [ ] **Step 4: 交互验证**

点开切换器选「海蓝」：主按钮、开关、菜单选中变蓝，popover 里勾选到海蓝；刷新后仍是海蓝；切回青瓷恢复。再切到海蓝后打开「角色管理 → 停用确认框」，确认主按钮也是海蓝（Review Focus 第 3 条），按钮文案不应出现「停 用」的空格。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/layouts/AdminLayout.vue
git commit -m "feat: 顶栏增加配色切换入口"
```

---

### Task 5: 规范同步与终验

**Files:**
- Modify: `skills/admin-frontend/SKILL.md`（技术节的颜色说明）

- [ ] **Step 1: 更新 skill**

把「主色 `#0E7C74`，侧栏 `#163033`…」一条改为：默认青瓷（主色 `#0E7C74`、侧栏 `#163033`、内容底 `#F2F5F4`），配色集中在 `src/theme/presets.ts`，用 `--accent`/`--ink`/`--paper` 等变量；组件里不要写死主题色；语义色和菜单三色标签固定。

- [ ] **Step 2: 同步 ~/.dsh 副本**

尝试 `cp skills/admin-frontend/SKILL.md ~/.dsh/skills/admin-frontend/SKILL.md`；若沙箱拒绝写入，记录并让用户手动复制。

- [ ] **Step 3: 终验**

Run: `cd frontend && npm run build`；随后启动 8000/5174，在 1440×900 下四套各截图一张，确认：无整页横向滚动条、语义色不变、切换即时、刷新保持。

- [ ] **Step 4: 提交**

```bash
git add skills/admin-frontend/SKILL.md
git commit -m "docs: 补充配色切换规范"
```
