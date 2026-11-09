# 管理端多配色（个人切换）设计

日期：2026-11-09
状态：已确认（2026-11-09）

## 意图

在现有青瓷色之外，提供几套可切换的配色。切换是个人偏好：存在浏览器里，点一下立即生效，不影响其他用户。

## 目标

- 4 套配色：青瓷（当前，默认）、海蓝、墨紫、赭石。
- 顶栏放配色按钮，点选即时切换；刷新后保持。
- 换肤范围覆盖「壳 + 主色」：主色、侧栏（含子菜单/悬停/选中）、内容底、顶栏、表头、斑马纹、页面里的浅色调块。
- 首屏就要用对配色，不能先闪一下青瓷色。

## 非目标

- 不做深色模式；四套都是浅色主题。
- 不做后端配置、不按用户存库；只存 `localStorage`。
- 不换语义色：成功 `#0E7C74`、失败 `#A33B32`、菜单三色标签（目录/页面/按钮）保持固定。
- 不改布局：侧栏宽度、折叠、手风琴、表格自适应都不动。

## 方案

- **A（选用）主题 store + CSS 变量 + AntD token**：一份 preset 同时喂给 `<html>` 的 CSS 变量和 `ConfigProvider`，颜色只有一个来源。
- C（未选）只换主色：改动小，但侧栏和内容底占比大，几套配色看着差别很小。
- 纯 CSS `data-theme` 方案：AntD 仍要 JS token，颜色维护两份，排除。

## 设计

### 配色数据（`src/theme/presets.ts`）

每套配色一个对象，字段即 CSS 变量名（去掉 `--`）：

`accent`、`ink`、`menuSub`、`menuHover`、`menuText`、`paper`、`sheet`、`line`、`text`、`muted`、`rowAlt`、`rowHover`、`headerBg`、`accentSoft`、`accountHover`、`loginHue`。

四套取值：

| 变量 | 青瓷 | 海蓝 | 墨紫 | 赭石 |
| --- | --- | --- | --- | --- |
| accent | `#0E7C74` | `#2563C9` | `#6A4C93` | `#A85A2A` |
| ink | `#163033` | `#14243D` | `#241C33` | `#33231B` |
| menuSub | `#102628` | `#0F1C31` | `#1B1527` | `#271A13` |
| menuHover | `#1D4548` | `#1C3253` | `#362A4B` | `#463225` |
| menuText | `#D7E4E2` | `#D6E1F2` | `#E2DBEC` | `#EDE0D6` |
| paper | `#F2F5F4` | `#F2F5FA` | `#F6F4F8` | `#F7F3EF` |
| sheet | `#FBFCFB` | `#FBFCFE` | `#FCFBFD` | `#FCFAF8` |
| line | `#D3DDDB` | `#D5DDE9` | `#DDD6E6` | `#E2D6CA` |
| text | `#162326` | `#16202E` | `#201A2A` | `#2A211B` |
| muted | `#5C6C6A` | `#556375` | `#5F566C` | `#6C5D52` |
| rowAlt | `#F3F7F6` | `#F3F6FB` | `#F5F2F8` | `#F6F1EB` |
| rowHover | `#EBF1EF` | `#EAF0F8` | `#EFEAF5` | `#F0E8E0` |
| headerBg | `#F7FAF9` | `#F6F9FD` | `#FAF8FC` | `#FAF6F2` |
| accentSoft | `#EEF6F5` | `#EDF3FC` | `#F1ECF7` | `#F7EEE6` |
| accountHover | `#E7EEED` | `#E4EBF4` | `#EAE4F1` | `#EBE1D6` |
| loginHue | `0deg` | `45deg` | `90deg` | `210deg` |

### 应用方式

- `useThemeStore`（Pinia）：`paletteId` 从 `localStorage('admin:theme')` 读，默认 `celadon`。
- store 初始化时同步把变量写到 `document.documentElement.style`，保证首屏正确；`setPalette(id)` 写变量 + 存 localStorage。
- 同时调用 `ConfigProvider.config({ theme, autoInsertSpaceInButton: false })`，让静态 `Modal.confirm` 也跟随主题（它不继承组件树里的 ConfigProvider）。
- `App.vue` 用 store 里的配色生成 AntD `ThemeConfig`（`colorPrimary`/`colorLink`/`colorBgLayout`/`colorText`/`colorBorder` + Menu/Layout 组件 token），替换现在写死的 `theme.ts` 常量；`theme.ts` 保留基础 token 和 `buildTheme(palette)`。
- CSS：`global.css` 的 `:root` 只留默认值，组件里改为 `var(--...)`；补 `--menu-sub`、`--menu-hover`、`--menu-text`、`--header-bg`、`--accent-soft`、`--account-hover`。替换 `AdminLayout.vue` 里写死的 `#163033`、`#f7faf9`、`#e7eeed`、`#f4f7f6`，以及 `dashboard`、`log` 详情里的浅色底。
- 登录页本来就用变量，自动跟随；背景 SVG 用伪元素承载并 `filter: hue-rotate(var(--login-hue))`，避免青绿光晕和蓝色/紫色主题打架。
- 语义色、菜单三色标签不改成变量。

### 切换入口（`AdminLayout.vue`）

顶栏右侧、用户下拉左边，加一个调色板图标按钮；点开 popover 列出四套配色：左侧三色小圆点（侧栏 / 内容底 / 主色）+ 名称 + 当前项打勾。点击即切换并关闭。按钮加 `aria-label="切换配色"`。

### 验收

- 四套配色可切换，按钮、链接、开关、分页、菜单选中、侧栏、顶栏、表格斑马纹、页面浅色块同步变化。
- 刷新后保持所选配色，首屏无青瓷色闪烁。
- 成功/失败文字、菜单三色标签在四套配色下都保持原色。
- 四套配色下文字/侧栏对比度可读，主按钮白字清晰。
- `npm run build` 通过；1440×900 下四套各截一张图。
