---
name: admin-frontend
description: >-
  Apply admin-console frontend conventions for Vue 3 and Ant Design Vue:
  full-width lists, two-column create/edit dialogs, permission buttons, and
  Chinese copy. Use when building or changing a 后台管理系统, 管理端, admin
  list, table, modal form, or Ant Design Vue page.
---

# 后台管理前端规范

面向 Vue 3 + Ant Design Vue 的中后台。改列表、弹窗、表单、布局、按钮权限时按本规范，不要换成 Element Plus。

## 技术

- Vue 3、TypeScript、Vite、Vue Router、Pinia、Axios、`ant-design-vue`
- `ConfigProvider` 设置中文语言包，并关闭按钮中文自动插空格（`autoInsertSpaceInButton: false`）
- 主色 `#0E7C74`，侧栏 `#163033`，内容底 `#F2F5F4`，文字 `#162326`，分割线 `#D3DDDB`
- 字体：`"IBM Plex Sans", "PingFang SC", "Microsoft YaHei", sans-serif`
- 圆角 8px。主按钮不要投影

## 壳

侧栏 + 顶栏 + 内容区。内容区是工作面，页面 `width: 100%`，不要给列表页设 `max-width`。

顶栏放折叠。当前用户收成下拉，里面是修改密码和退出。页面标题放在内容区的 `h1`，不要和顶栏重复一遍。

## 列表

表格必须铺满内容区，列宽随容器伸缩。

- 表格 `width: 100%`，`table-layout: fixed`
- 单元格单行，超出省略（`white-space: nowrap; overflow: hidden; text-overflow: ellipsis`）
- 不要用 `scroll.x = 'max-content'`，那会把表格缩成内容宽度，右侧留空
- 工具条：筛选在左，主操作（新增）在右
- 查询按钮文案是「查询」

Ant Design 会给 table 写内联 `table-layout: auto`，固定布局必须加 `!important` 才能压过它：

```css
.page .ant-table-content > table {
  width: 100% !important;
  table-layout: fixed !important;
}
```

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
