# INIT-002：Python 开发环境与基础 CI

- 日期：2026-10-17；状态：已实现本地基础能力，待人工验收及 GitHub Actions 实测。
- 来源：用户明确任务及 Windows + VS Code / 华为云 Ubuntu 补充确认；任务书第三节；关联 ENG-04、ENG-09。
- 负责人、人工评审人：待团队填写；AI 参与：方案、代码、配置、文档与本地验证。
- 当前分支：`chore/INIT-002-dev-environment`。未执行 Git 提交、推送、合并或部署。
- 前置条件：根目录文档及领域边界；同步依赖需可访问 Python 下载源和 PyPI。

## 范围、实现与验收

| 验收条件 | 实现 | 验证 |
| --- | --- | --- |
| 统一 Python 3.12 和 uv 环境 | [pyproject](../../pyproject.toml)、[锁文件](../../uv.lock)、[Python 版本](../../.python-version) | locked sync 成功，uv 0.13.1，Windows Python 3.12.15 |
| M1/M2/M3 可启动并返回健康状态 | [M1](../../backend/modules/m1/main.py)、[M2](../../backend/modules/m2/main.py)、[M3](../../backend/modules/m3/main.py)、[约定](../../contracts/health.md) | 三个真实 Uvicorn HTTP 请求均得到 200、JSON 和 status=ok |
| 真实行为与错误路径测试 | 三个模块的 `tests/test_health.py` | 每模块 GET 200、POST 405、未知路径 404；共 9 项 |
| 本地与 CI 共用检查 | [CI](../../.github/workflows/ci.yml)、根 pytest/Ruff 配置 | Windows 本地执行；Ubuntu 托管结果待后续 Actions |
| 忽略敏感与临时产物 | [.gitignore](../../.gitignore) | 检查虚拟环境、环境变量文件、密钥扩展名及缓存等规则 |
| 可复现操作说明 | [根 README](../../README.md#本地开发与基础验证) | 使用根目录相同 uv 命令，源码与 CI 不依赖平台专有行为 |

## Windows 实际执行证据

本机 uv 不在 PATH，实际命令通过临时工具目录下的 uv.exe 调用，参数与 README/CI 一致。Python、uv 工具及包下载在获批的沙箱外执行；uv 默认用户缓存锁文件在沙箱内不可写，因此最终 uv 检查也在获批的沙箱外执行。uv 工具与 PDF 阅读工具安装在系统临时目录，未加入项目依赖。

1. `uv python install 3.12`：安装 CPython 3.12.15。
2. `uv sync --dev`：生成锁文件和根 `.venv`，解析 25 个项目/包记录，安装 24 个第三方包。跨磁盘缓存导致硬链接降级为复制，仅影响安装性能。
3. `uv sync --locked --dev`：成功，确认锁文件与配置一致。
4. `uv run --locked ruff check .`：通过。
5. `uv run --locked ruff format --check .`：通过。
6. `uv run --locked pytest`：9 项通过。真实执行 FastAPI ASGI 路由，没有 mock。
7. 网络验证：用根 `.venv` 的 Python 分别执行 `python -m uvicorn backend.modules.<m1|m2|m3>.main:app --host 127.0.0.1 --port <临时空闲端口>`，逐一通过 HTTP GET 检查状态码、JSON 类型与响应体。3/3 通过；finally 中终止并等待所有本次子进程。
8. 故障注入：临时将 M1 的 `status=ok` 改为 `status=broken`，执行 `python -m pytest backend/modules/m1/tests/test_health.py -q`，结果 1 failed、2 passed，退出码 1，失败发生在响应体断言。finally 逐字节恢复文件，再运行完整基础检查。故障注入运行另有两条 pytest 缓存权限警告，属于沙箱访问限制，不是用来触发测试失败的原因。
9. 恢复后最终检查：locked sync、Ruff lint 和格式检查全部通过；完整 pytest 再次得到 9 passed、1 warning（0.83 秒）。
10. `git check-ignore` 验证虚拟环境、环境配置、密钥和临时缓存被忽略，`uv.lock`、`.python-version`、`.env.example`、`.env.test.example` 可纳入版本管理；38 个本地 Markdown 链接目标均存在。`git diff --check` 通过，仅有 Git 按本机配置提示未来 LF/CRLF 转换，无空白错误。

锁定主要包：FastAPI 0.143.3、Uvicorn 0.54.0、pytest 9.1.1、httpx 0.28.1、Ruff 0.17.1、Starlette 1.8.0。正常测试产生一条 `StarletteDeprecationWarning`：上游 TestClient 提示未来改用 httpx2；当前所有行为通过，未屏蔽警告，后续升级时评估兼容性。

## 未完成与风险

Ubuntu CI 与 GitHub Windows CI 尚未运行，不能用本地结果代替托管结果。本次不提交或推送，未安装 gh CLI，也未核实远程分支保护；负责人需在 GitHub 配置双平台必需检查和人工评审。

Python 固定为 3.12 系列，补丁版本可能随安装源更新；包版本固定在共享锁文件，包含平台条件和发行文件，不复制 Windows 虚拟环境到 Ubuntu。项目命令无需激活脚本、绝对路径或手工修改 sys.path。

没有预约/审批/报修业务、D 实现、数据库表、迁移、前端或生产部署。本次网络验证仅验证入口存活，不代表课程要求的跨模块业务写回已经实现。完整构建交付、业务测试、测试服务器自动部署、生产审批和迁移验证继续保留为待完成需求。[ADR-0002](../adr/0002-python-environment-and-ci.md) 待团队评审。
