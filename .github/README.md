# 协作与自动化预留

已创建 [Backend CI](workflows/ci.yml)：所有 PR 和 main Push 触发 Windows/Ubuntu 矩阵，使用统一 Python 3.12 配置、uv 0.13.1 和根锁文件，依次执行 `uv sync --locked --dev`、`uv run --locked ruff check .`、`uv run --locked ruff format --check .`、`uv run --locked pytest`。检查失败则 job 失败，权限仅 contents:read，Actions 引用固定提交。运行结果以 GitHub Actions 实际记录为准。

尚未创建 PR 模板或 CODEOWNERS，未核实远程保护设置。负责人需将双平台检查设为必需并要求人工评审；仅添加 YAML 不能阻止合并。

跨模块/D/schema 组内评审。完整构建交付、测试自动部署、生产审批及迁移/插件交付仍为后续工作；当前 CI 不部署。后续需保留版本与回滚证据并协调部署窗口。

PR 包含任务/需求、行为、影响、兼容、验证、迁移/发布风险及未完成项。AI 变更人工验收后提交，冲突由人处理。保护规则是托管平台设置，文档存在不表示已经启用。
