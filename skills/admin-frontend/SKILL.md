---
name: admin-frontend
description: >-
  Apply admin-console frontend conventions for Vue 3 and Ant Design Vue:
  full-width responsive tables, status switches, two-column create/edit
  dialogs, colored menu-type tags, permission buttons, and Chinese copy. Use
  when building or changing a 后台管理系统, 管理端, admin list, table, modal
  form, or Ant Design Vue page.
---

# 后台管理前端规范

面向 Vue 3 + Ant Design Vue 的中后台。改列表、弹窗、表单、布局、按钮权限时按本规范，不要换成 Element Plus。

## 技术

- Vue 3、TypeScript、Vite、Vue Router、Pinia、Axios、`ant-design-vue`
- `ConfigProvider` 设置中文语言包，并关闭按钮中文自动插空格（`autoInsertSpaceInButton: false`）
- 默认青瓷配色：主色 `#0E7C74`、侧栏 `#163033`、内容底 `#F2F5F4`、文字 `#162326`、分割线 `#D3DDDB`
- 另有海蓝、墨紫、赭石、皓白四套配色（皓白是白色侧栏 + 石墨主色），定义在 `src/theme/presets.ts`；通过 `--accent`/`--ink`/`--paper`/`--header-bg` 等 CSS 变量切换，组件里不要写死主题色
- 语义色不随主题变：成功 `#0E7C74`、失败 `#A33B32`；菜单三色标签也固定
- 字体：`"IBM Plex Sans", "PingFang SC", "Microsoft YaHei", sans-serif`
- 圆角 8px。主按钮不要投影

## 颜色与标签

语义色只表达状态，不要拿来做装饰。

| 语义 | 颜色 | 用在哪 |
| --- | --- | --- |
| 成功 / 正常 | `#0E7C74`（固定） | 只读结果的文字 |
| 失败 / 停用 / 异常 | `#A33B32`（固定） | 只读结果的文字 |
| 停用中的开关 | antd 默认灰 | 开关本身不染色，避免和主色抢 |

只读结果用文字色，不要做成标签墙或开关：

```vue
<span class="status" :data-ok="ok">{{ ok ? '成功' : '失败' }}</span>
```

```css
.status[data-ok='true'] {
  color: #0e7c74;
}
.status[data-ok='false'] {
  color: #a33b32;
}
```

菜单的三种类型固定用三色标签，列表和分配菜单共用同一个 `.type-tag`：

| 类型 | 文字色 | 背景 |
| --- | --- | --- |
| 目录 | `#1B5FC1` | `#ECF3FF` |
| 页面 | `#0B6B64` | `#E6F4F1` |
| 按钮 | `#A85A00` | `#FFF2E0` |

```css
.type-tag.ant-tag {
  margin-inline-end: 0;
  padding: 0 7px;
  border: 0;
  font-size: 12px;
  line-height: 20px;
}
.type-tag.type-directory {
  color: #1b5fc1;
  background: #ecf3ff;
}
.type-tag.type-menu {
  color: #0b6b64;
  background: #e6f4f1;
}
.type-tag.type-button {
  color: #a85a00;
  background: #fff2e0;
}
```

标签里写清楚「目录」「页面」「按钮」，不要只靠颜色区分；这组样式放在 `src/styles/global.css`，不要每个页面各写一份。

## 壳

侧栏 + 顶栏 + 内容区。内容区是工作面，页面 `width: 100%`，不要给列表页设 `max-width`。

顶栏放折叠。当前用户收成下拉，里面是修改密码和退出。页面标题放在内容区的 `h1`，不要和顶栏重复一遍。

侧栏菜单是手风琴：同一时间只展开一个一级目录；进入页面时自动展开它所属的目录，其它目录收起。

顶栏右侧（用户下拉左边）放配色切换，四套配色即时生效，选择存 `localStorage`（个人偏好，不落库）。

## 列表

表格必须铺满内容区，列宽随容器伸缩。

- 表格 `table-layout: fixed`，单元格单行，超出省略（`white-space: nowrap; overflow: hidden; text-overflow: ellipsis`）
- 宽度交给 `scroll.x`（见下文「表格自适应」）。不要用 `scroll.x = 'max-content'`，也不要用 `width: 100% !important` 压掉 antd 的内联宽度
- 工具条：筛选在左，主操作（新增）在右
- 查询按钮文案是「查询」

Ant Design 会给 table 写内联 `table-layout: auto`，固定布局必须加 `!important` 才能压过它：

```css
.page .ant-table-content > table,
.page .ant-table-header > table,
.page .ant-table-body > table {
  table-layout: fixed !important;
}
```

## 表格自适应

表格要同时吃满高度和宽度，两件事分开处理：高度靠表体自己滚，宽度靠列宽 + 表内横向滚动。整页不能出现横向滚动条。

### 高度：表体滚，分页钉底

- 列表页根节点写 `class="page page-fill"`；页头、工具条 `flex: none`，只让表格区域吃剩余高度
- 表格外层 `<div ref="tableWrap" class="page-fill-body table-fill">`，让卡片撑满内容区
- `scroll.y` 用 `useTableHeight(容器 ref)` 实测（容器高 − 表头 − 分页 − 边框），不写死数字，也不用 `calc(100vh - N)`
- 数据 0 行、1 行、满页时卡片高度一致；分页始终在卡片底部，窗口再矮也不会掉出视口
- 表头固定，只有表体滚动

```vue
<div ref="tableWrap" class="page-fill-body table-fill">
  <a-table :scroll="{ x: 900, y: tableY }" … />
</div>
```

```ts
import { ref } from 'vue'
import { useTableHeight } from '@/utils/useTableHeight'

const tableWrap = ref<HTMLElement | null>(null)
const tableY = useTableHeight(tableWrap)
```

`page-fill` / `page-fill-body` / `table-fill` 定义在 `src/styles/global.css`。

### 宽度：数字 scroll.x + 固定操作列

- `scroll.x` 写所有列 `width` 之和（数字），不写 `'max-content'`
- 容器比 `scroll.x` 宽：表格自动铺满（antd 写入的 `min-width: 100%`），列宽按比例摊开
- 容器比 `scroll.x` 窄：在表格卡片内部横向滚动，不裁列、不撑破页面
- 每列都给 `width`；文本列加 `ellipsis: true`
- 操作列 `fixed: 'right'`，宽度按按钮实际占用给足（编辑 / 执行 / 日志 / 删除约 220），窄屏滚动时始终可见
- 固定列左侧加一条 1px 分隔线（`.ant-table-cell-fix-right-first`），滚动被盖住时不会像被裁掉
- 侧栏在 1200px 以下自动收起（`breakpoint="xl"`），给表格让出宽度

### 验收

- 1440×900、1180×760、1024×700 三档：没有整页横向滚动条（`document.documentElement.scrollWidth === clientWidth`），分页可见，最右操作列不被裁切
- 数据 0 行、1 行、满页切换时卡片高度不跳变
- 表体滚动时表头不动；横向滚动时操作列不动

## 开关

两种对立状态、而且切换会改变真实数据的地方，用 `a-switch`，不要用下拉框或纯文字：

- 账号停用、角色停用、定时任务启停、菜单显示/状态、谷歌验证开关
- 能放列表里就在列表里直接切换（`状态` 列），配专用的状态接口（`PATCH /.../status`），不要为了改一个状态提交整个表单
- 表单里的这类字段同样用开关，不要用 `a-select` 的「正常/停用」
- 危险方向（停用/关闭）二次确认；成功提示与开关方向一致：已启用 / 已停用
- 没有更新权限时降级为文字，不要留空白
- 开关切换期间禁用当前行的开关（`rowBusy`），避免连点
- 开关文案控制在两个字：正常 / 停用、启用 / 关闭；状态列宽留到 110 左右，别把开关压成省略号
- 状态列要补充说明时，开关用 `.cell-switch`（`flex`，`gap: 8px`），下方说明用 `.sub`（12px，`--muted`）

只是展示结果、不能操作的字段保持文字或标签，不要做成开关：

- 操作日志的成功/失败、任务执行结果、上次执行状态与时间

## 弹窗

字段少（例如只重置密码）保持单列、默认宽度。

新增和编辑字段多时，弹窗宽 720–760，表单左右两列：

```css
.form-grid.ant-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 24px;
  align-items: start;
}
.form-grid .span-2 {
  grid-column: 1 / -1;
}
.form-grid .ant-input-number,
.form-grid .ant-select {
  width: 100%;
}
@media (max-width: 720px) {
  .form-grid.ant-form {
    grid-template-columns: 1fr;
  }
}
```

- 表单加 `class="form-grid"`，`layout="vertical"`
- 输入框、选择器、数字框在格子里拉满
- 菜单树、多行文本、需要整行的多选，加 `class="span-2"`
- 确定是「保存」，取消是「取消」
- 校验失败时弹窗保持打开（`@ok` 返回 reject）
- 成功提示与按钮同词：保存 → 「已保存」，删除 → 「已删除」，停用 → 「已停用」
- 内容可能超长时给 body 加 `max-height` + `overflow-y: auto`，保存/取消始终留在底部

## 分配菜单

角色分配菜单不要用一棵无限展开的树，改成「目录分组 + 页面行 + 按钮横向」：

- 目录做分组标题，带蓝色「目录」标签；页面单独一行，带青色「页面」标签和等宽字体的路径
- 页面下的按钮权限横向排列（`display: flex; flex-wrap: wrap; gap: 6px 20px`），按钮文字用橙色，组前放一个橙色「按钮」标签
- 勾按钮自动勾上所属页面；取消页面时连同按钮一起取消；目录标题的复选框做整组全选，部分选中用 `indeterminate`
- 弹窗顶部放「全选」和一句说明（勾选页面才出现在导航，按钮决定操作权限）
- 弹窗 body 限高滚动（`max-height: 60vh; overflow-y: auto`），保存/取消常驻底部

```css
.perm-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 20px;
  align-items: center;
  margin: 6px 0 0 24px;
}
.perm-button-name {
  color: #a85a00;
}
```

## 权限与文案

- 按钮用 `v-permission="'模块:资源:动作'"`，例如 `system:user:create`
- 无权限就去掉按钮。隐藏只影响界面，接口仍要校验
- 页面里不要散落 `if (role)`
- 界面用中文。按钮写动作本身：查询、新增用户、编辑、删除、停用、启用、保存
- 空状态和错误说明发生了什么、接下来怎么做，不写空泛道歉

## 新页面

1. 页面放在 `src/views/<模块>/<资源>/index.vue`，菜单的组件字段与该路径一致，不含 `.vue`
2. 列表页结构：`h1`、工具条、表格
3. 请求按资源放在 `src/api/`，页面不直接拼 URL
4. 工作台用静态示例：一组铺满宽度的数字和一张写死的表格，标明没有请求接口。不要接真实统计接口，也不要做成带投影的指标卡片
