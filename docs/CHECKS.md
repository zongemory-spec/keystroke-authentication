# 本次整理与验证

日期：2026-10-31。此文件记录本地验证，不表示对应 GitHub 提交已经运行成功。

## 范围

- 将未使用的模型代码与命名清理，现用服务改名为 archiveService。
- Tailwind 通过 npm 依赖与 PostCSS 本地编译，使用系统字体。
- 正常登录、恒真式和注释截断分别标记模拟分支，并显示对应说明。
- 页面状态明确表示合成数据与本地规则模拟。

## 检查

- `npm run build` 执行 TypeScript 检查与 Vite 生产构建。
- 五个函数级场景：正常账号密码、错误密码、恒真式、注释截断、引号错误。
- 浏览器检查错误密码反馈、正常登录和本地档案、快捷示例及漏洞手册。
- 生产 HTML 的资源链接不包含外部 HTTP(S) 地址，CSS 随构建生成；不再请求 Tailwind CDN 与 Google Fonts。

模拟器的原有规则未改成真实 SQL 引擎；仍存在模式匹配的教学简化。标记 normal/tautology/comment 是说明命中的模拟分支，不是安全检测或数据库执行证明。

## 更新旧仓库

网页上传只新增或覆盖文件，不能删除旧文件。上传完成后，在 GitHub 删除：

```text
servicce/geminiService
services/geminiService.ts
```

不删除 services/archiveService.ts；App.tsx 已改为引用它。Git 目录不会保存空目录，删除唯一文件后 servicce 会自然消失。

不要上传 node_modules/ 或 dist/。如部署 Pages，构建命令 npm run build、输出目录 dist。没有配置自动网站部署时，GitHub Actions 通过仅表示检查通过。
