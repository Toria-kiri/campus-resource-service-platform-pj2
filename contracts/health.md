# 最小健康检查约定

- 任务：INIT-002；关联 ENG-04、ENG-09；AI 草案待人工验收。
- 提供方：M1、M2、M3 各自的 FastAPI 应用；调用方：开发者、基础测试。
- `GET /health` 无请求体、无需凭据，返回 HTTP 200、`Content-Type: application/json` 和 `{"status":"ok"}`。
- 当前仅表示进程可响应请求，不检查数据库、依赖或业务就绪状态；不返回配置或敏感信息。
- `POST /health` 返回 HTTP 405 和 `{"detail":"Method Not Allowed"}`，Allow 包含 GET；未知路径返回 HTTP 404 和 `{"detail":"Not Found"}`。
- 无状态、只读、幂等，无写回、补偿、来源记录或时区字段；当前没有业务调用方与迁移步骤。
- 验证：各模块 `tests/test_health.py` 使用真实 ASGI 路由；本地网络启动证据见 [INIT-002](../docs/requirements/INIT-002-dev-environment.md)。

此约定不替代未来 M2/M3 → M1 的业务契约；后续变更需同步测试与文档并接受人工评审。
