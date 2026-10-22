# 校园资源服务平台

六人协作的《软件过程管理与工程伦理》课程实践项目（PJ）。以自习座位预约为核心，连接校园空间申请与物业维护，提升资源利用率，并形成可审查的人机协作、测试、发布和伦理实践证据。

需求依据：[课程任务书及附件 1](docs/requirements/Pj-任务书.pdf)（2026-10-08，共 6 页）。课程重视规划、验证与可交付过程；自然语言业务代理是附加项，不替代主功能和工程化要求。

## 当前状态

已初始化 Python 3.12 + uv 统一后端环境、M1/M2/M3 最小 FastAPI 入口、健康检查、pytest 与 Ruff，以及 Windows/Ubuntu 双平台基础 CI 配置。预约、审批、报修及 D 业务均未实现；没有数据库表、迁移、Docker 或部署配置。验证证据见 [INIT-002 任务记录](docs/requirements/INIT-002-dev-environment.md)，Ubuntu CI 是否通过以 GitHub Actions 实际运行结果为准。AI 变更待人工验收。

## 功能范围

| 模块 | 计划职责 |
| --- | --- |
| M1 自习座位预约 | 条件搜索、整点小时预约（单次最多 4 小时，可配置）、签到、提醒、违约、历史复用与运营查询 |
| M2 整教室预约与审批 | 权限门槛、申请、多级通过/驳回、超时自动撤销、座位占用写回 |
| M3 物业报修工单 | 故障上报、派单、维修中、超时升级、完工验收与评价、维修下架写回 |
| D 公共层 | RBAC、空间与座位主数据、开放时间/配置、通知、操作审计 |

附件还要求院系自习室的访问限制、管理员登记/注销空间与座位、插座特殊标记、每日关联教室的动态签到编码；预约前 15 分钟和开始后 10 分钟提醒，开始后 15 分钟未签到则取消、释放、提醒并记违约。详见[初始需求追踪](docs/requirements/README.md)。M2/M3/D 仍需细化业务规则及验收标准。

## 技术与架构

本次确认的后端工具为 Python 3.12、uv 0.13.1、FastAPI、pytest、Ruff，依赖精确版本见根目录 `uv.lock`。六名成员日常使用 Windows + VS Code，目标部署系统为华为云 Ubuntu；基础 CI 同时验证 Windows 和 Ubuntu。Vue 3 + TypeScript、PostgreSQL、Docker、华为云仍为后续技术规划，前端具体版本、迁移工具和云资源尚未选定。

根目录单一 `pyproject.toml`、`uv.lock` 和 `.venv` 管理后端依赖，开发依赖归入 `dev` 组，不将每个领域目录包装为独立发布包。依据与备选见 [ADR-0002](docs/adr/0002-python-environment-and-ci.md)（待团队评审）。

## 本地开发与基础验证

以下命令均在仓库根目录执行。Windows PowerShell 与 Ubuntu shell 使用相同的 uv 命令，无需激活虚拟环境或设置 `PYTHONPATH`。

先按 [uv 官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)安装 uv 0.13.1。Windows 已有 Python 和 pip 时可执行 `py -m pip install uv==0.13.1`，安装后确认 `uv --version`。项目所需 Python 由 uv 安装，不要求系统默认版本已为 3.12。

```text
uv python install 3.12
uv sync --locked --dev
uv run --locked python --version
```

VS Code 打开仓库根目录，安装 Microsoft Python 扩展，通过“Python: Select Interpreter”选择根目录 `.venv`：Windows 为 `.venv/Scripts/python.exe`，Ubuntu 为 `.venv/bin/python`。不将本机绝对路径写入共享配置。

拉取依赖变更后执行 `uv sync --locked --dev`。新增或升级依赖时显式更新配置与锁文件，并将两者一起交付评审：

```text
uv add <依赖名>
uv add --dev <开发依赖名>
uv lock --upgrade-package <依赖名>
uv sync --locked --dev
```

本地与两个 CI 平台使用相同检查：

```text
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

修正格式使用 `uv run --locked ruff format .`，随后检查差异。pytest 通过 importlib 模式收集同名模块测试，路径配置集中在 `pyproject.toml`。

在三个终端中分别启动应用（端口仅为本地开发约定）：

```text
uv run --locked uvicorn backend.modules.m1.main:app --reload --port 8001
uv run --locked uvicorn backend.modules.m2.main:app --reload --port 8002
uv run --locked uvicorn backend.modules.m3.main:app --reload --port 8003
```

分别访问 `http://127.0.0.1:8001/health`、`http://127.0.0.1:8002/health`、`http://127.0.0.1:8003/health`，均应返回 HTTP 200 和 `{"status":"ok"}`。约定见 [health 契约](contracts/health.md)。Ctrl+C 停止服务。当前应用没有数据库或环境变量要求；真实密钥不进入仓库。

基础 CI 在所有 PR 及 `main` Push 时运行，使用 Windows/Ubuntu 矩阵、同一 `.python-version`、固定 uv 版本和 `uv.lock`，依次同步依赖、检查代码与格式、运行 pytest。GitHub 分支保护还需将两个矩阵检查设为必需并要求人工评审；当前未核实远程保护设置。

采用 Monorepo，前后端分离，后端按 M1/M2/M3/D 组织。模块目录不等于已经确定的微服务。跨模块业务通过公开网络 API 交互，禁止访问其他模块内部服务或数据表，以支持任务书要求的真实网络调用演示。进程数量、路由/网关、数据库物理隔离及一致性方案待 ADR 确认。

D 管理空间/座位身份与基础属性，M1 管理预约与有效可用状态；具体数据所有权在实现前细化，避免两个权威来源。D 的人员归属尚未决定。

| 链路 | 要求 |
| --- | --- |
| M3 → M1 | 自习室存在维修中工单时全室座位下架；验收通过撤销对应工单限制 |
| M2 → M1 | 审批通过占用全室指定时段；驳回或超时撤销时撤销对应申请占用 |
| M1 追溯 | 记录来源 M1/M2/M3、来源业务记录、目标、时段、操作及关联标识 |

恢复或回滚只撤销对应来源的限制，再计算可用性，不能覆盖其他工单、教室占用或个人预约。冲突、重复请求、失败重试、顺序和补偿先写入[契约](contracts/README.md)，再实现。

`plugins/` 为附加自然语言业务代理保留独立安装、配置、调用与交付空间。任务书建议接入 DeepSeek Harness（DSH）；本次不选定 SDK、协议或框架。插件只调用公开 API，沿用权限/审计，不直连业务库、不复制业务逻辑，未来将构建、安装、配置、调用验证和部署纳入 CI/CD。

## 当前目录

以下展示主要目录；另有根目录 `pyproject.toml`、`uv.lock`、`.python-version` 和 `.github/workflows/ci.yml`，M1/M2/M3 各有 `main.py` 和 `tests/test_health.py`。

```text
.
├── README.md
├── AGENTS.md
├── .gitignore
├── .gitattributes
├── .github/README.md
├── frontend/README.md
├── backend/
│   ├── README.md
│   └── modules/
│       ├── m1/README.md
│       ├── m2/README.md
│       ├── m3/README.md
│       └── d/README.md
├── contracts/README.md
├── tests/README.md
├── database/
│   ├── migrations/README.md
│   └── seeds/README.md
├── ops/README.md
├── plugins/README.md
└── docs/
    ├── requirements/
    │   ├── Pj-任务书.pdf
    │   └── README.md
    ├── adr/
    │   ├── README.md
    │   └── 0001-repository-boundaries.md
    └── ethics/README.md
```

| 目录 | 职责 |
| --- | --- |
| frontend | Web 页面、功能分区及共享 UI 基础设施 |
| backend/modules | 四个领域的服务实现和模块内单元测试，D 不收容任意业务逻辑 |
| contracts | 公开 API、跨模块交互、错误与兼容性约定，后续加入可验证 OpenAPI 描述 |
| tests | 契约、真实跨模块集成、端到端与迁移验证，不重复模块内单元测试 |
| database/migrations、seeds | 有序版本化结构演进与幂等初始化数据，均标注所属模块 |
| ops | 后续容器、环境模板、华为云基础设施/部署脚本与发布回滚记录 |
| .github | Windows/Ubuntu 基础 CI；PR 模板和平台保护设置仍待完善 |
| plugins | 独立插件包及安装、配置、调用、构建/部署约定 |
| docs/requirements、adr、ethics | 需求验收追踪、架构决策、持续伦理分析与证据 |

## 协作与版本管理

建议六人分为三个模块组，每组约两人认领 M1/M2/M3；前端、D、契约和发布责任由团队平衡分配。名单尚未确认。D 归属须记录候选方案、工作量均衡、契约治理、故障责任、依据及达成一致过程。

建议 `main` 为可交付主线，短生命周期分支 `feat/<需求ID>-<描述>`、`fix/<需求ID>-<描述>`、`docs/<任务ID>-<描述>`，不预设长期开发分支。提交写明任务/需求、变更和原因；AI 变更须人工验收后提交，持续保留提交历史，聊天记录不能替代。**代码冲突由人处理，AI 不得自行解决或合并冲突。**

PR 至少一名人工评审者；跨模块、D、schema 变更邀请相关负责人经组内评审。未来启用分支保护和测试门禁，测试失败禁止合并。发布 tag 关联提交、镜像、迁移版本与发布说明，能确认当前运行版本。规则见 [AGENTS.md](AGENTS.md)。

## Git 协作与提交规范

为保证六人协作开发过程清晰、可追踪、可审查，本项目统一使用功能分支开发、约定式提交（Conventional Commits）和 Pull Request（PR）评审机制。

### 1. 分支管理策略

项目采用简化的功能分支工作流：

- `main` 为主分支，保存经过评审和验证的代码。
- 每项独立开发任务从最新的 `main` 创建新分支。
- 同一任务可以包含多个相关 Commit，不需要每次 Commit 都创建新分支。
- 开发完成后，将分支推送到 GitHub，通过 PR 申请合并到 `main`。
- PR 必须经过至少一名其他组员的人工评审，满足已配置的质量检查要求后才能合并。
- 涉及跨模块接口、公共层或数据库 Schema 的变更，应邀请相关模块负责人共同评审。
- 不直接向 `main` 提交普通开发变更，不绕过 PR 评审。
- Git 合并冲突由组员人工处理，AI 可以辅助分析，但不得自行解决冲突或执行冲突合并。
- PR 合并后，可以删除已完成任务的远程分支。

推荐的开发流程：

```text
同步最新 main
    ↓
创建任务分支
    ↓
开发并进行相关测试
    ↓
提交一个或多个 Commit
    ↓
推送任务分支至 GitHub
    ↓
创建 Pull Request
    ↓
人工代码评审 + 自动化检查
    ↓
合并到 main
    ↓
删除已合并的任务分支
```

### 2. 分支命名规范

统一采用以下格式：

```text
<type>/<task-id>-<short-description>
```

各字段含义：

- `type`：任务类型，使用小写英文前缀。
- `task-id`：任务编号，例如 `INIT-001`、`M1-001`、`M2-001`、`M3-001`、`D-001`。
- `short-description`：简短英文描述，使用小写字母及连字符 `-` 分隔单词。

分支类型原则上与 Commit 类型保持一致；一个任务涉及多种文件变更时，分支类型以主要任务目标为准。

示例：

```text
chore/INIT-001-project-setup
feat/M1-001-seat-reservation
feat/M2-001-room-approval
feat/M3-001-repair-order
feat/D-001-rbac
fix/M1-002-booking-conflict
docs/DOC-001-api-specification
test/M1-003-reservation-tests
ci/DEVOPS-001-github-actions
refactor/M2-002-approval-service
```

任务编号由团队统一管理，同一任务的分支、需求记录、PR 应使用一致的任务 ID。

### 3. Commit Message 规范

本项目采用 Conventional Commits（约定式提交）规范。

提交信息由 Summary（标题）和可选的 Description（正文）组成。

格式：

```text
<type>(<scope>): <中文简要描述>

<中文详细描述>
```

其中：

- `type`：必填，使用约定的英文类型前缀。
- `scope`：可选，表示影响的模块或范围，例如 `m1`、`m2`、`m3`、`d`、`frontend`、`backend`。
- 标题描述：必填，统一使用中文，简洁说明本次修改。
- 正文：可选，统一使用中文，说明修改内容、原因及必要的影响。
- 涉及具体任务时，应在 Commit 正文或关联 PR 中标注任务 ID。

#### Commit 类型

| 类型 | 使用场合 |
|---|---|
| `feat` | 新增功能或业务能力 |
| `fix` | 修复 Bug 或错误行为 |
| `docs` | 修改 README、AGENTS.md、需求文档、API 文档等 |
| `style` | 调整代码格式、缩进、空格等，不改变程序行为 |
| `refactor` | 重构代码结构，不新增功能或修复 Bug |
| `perf` | 优化程序性能 |
| `test` | 新增、修改或完善测试 |
| `build` | 修改依赖、构建系统、打包配置等 |
| `ci` | 修改 GitHub Actions 等持续集成和部署流水线 |
| `chore` | 项目初始化、日常维护及其他不属于上述类型的工程事务 |
| `revert` | 撤销先前的提交 |

以上是本项目约定使用的类型集合，并非 Conventional Commits 规范要求的唯一类型集合。

#### Commit 示例

**示例 1：初始化项目**

```text
chore: 初始化项目目录结构与开发规范
```

**示例 2：新增功能**

```text
feat(m1): 实现自习座位查询功能
```

**示例 3：修复问题**

```text
fix(m1): 修复重复预约导致的座位冲突
```

**示例 4：更新文档**

```text
docs: 补充 Git 分支与提交规范
```

**示例 5：新增测试**

```text
test(m3): 增加维修状态写回的集成测试
```

**示例 6：修改 CI/CD**

```text
ci: 添加 Pull Request 自动测试工作流
```

对于内容较多的提交，建议补充正文：

```text
feat(m1): 实现座位预约接口

- 增加座位预约的输入校验
- 检查预约时间段是否存在冲突
- 增加对应的单元测试

关联任务：M1-002
```

#### 破坏性变更

如果修改破坏了已有接口或兼容性，应明确标识 Breaking Change，并在 PR 中说明影响及迁移方案。

示例：

```text
feat(m1)!: 调整座位预约接口的数据格式

BREAKING CHANGE: 原预约时间字段已替换，
旧版本调用方需要同步更新。
```

### 4. Commit 编写要求

- 使用约定的英文类型前缀，描述统一使用中文。
- 一个 Commit 应围绕一个明确的修改目的，避免混入无关变更。
- Summary 应描述实际完成的修改，避免使用“修改代码”“更新文件”等含糊表述。
- 复杂变更应通过正文说明修改原因、主要内容和影响。
- 不得提交密钥、虚拟环境、构建缓存或无关临时文件。
- AI 生成的变更必须经过人工检查，不能仅根据 AI 的完成声明直接合并。

### 5. Pull Request 规范

PR 标题建议与 Commit Message 使用相同风格：

```text
<type>(<scope>): <中文描述>
```

每个 PR 至少包含：

- **关联任务**：任务 ID、需求 ID 或对应 Issue。
- **变更说明**：本次实现或修改的内容及原因。
- **验证结果**：已执行的测试及结果，未执行的检查需说明原因。
- **影响范围**：涉及的模块、API、数据库或部署配置。
- **待确认事项**：尚未完成的工作、已知风险或需要评审的决策。

PR 经人工评审并通过要求的检查后，方可合并到 `main`。

团队应在 GitHub 中配置相应的分支保护和状态检查。README 中的流程约定不代表平台保护功能已经启用。

## 环境与部署规划

开发、测试、生产环境由本组独占、组内模块共用；配置、数据和凭据隔离。模板进仓库，真实密钥使用本地环境或 CI/云密钥管理；禁止真实学生资料、凭据、生产数据入库。

已提供统一版本配置、锁文件和本地启动方式，后续再加入 Docker 与华为云 Ubuntu 基础设施脚本。结构仅由版本化迁移演进，空库可完整重放、重跑安全；种子数据幂等且与业务数据分离。迁移工具、隔离和恢复策略先评审。

当前 Actions 配置只覆盖 PR 和 main Push 的基础检查与测试；托管执行结果、必需检查及人工评审保护仍需在 GitHub 核实。后续补充构建交付、测试环境自动部署、生产人工审批与回滚，并协调发布顺序，通过部署窗口或等效机制避免集成误报。迁移与插件交付逐步纳入流水线。

课程不设统一完成日期：启动确认分工与 D 归属；第一次 Review 提交需求基线、任务依赖、架构/首轮功能、AI 规则和风险；第二次 Review 打通主功能/集成、迁移流水线和提交到部署流程；期末现场演示新环境部署、变更触发构建测试、schema 演进、生产发布/回退、一次网络跨模块写回。完成附加项则再演示会话操作。

# 团队开发环境与依赖同步操作手册

**适用项目：** 校园资源服务平台  
**适用人员：** M1、M2、M3 及公共模块 D 的所有开发成员  
**开发环境：** Windows + VS Code + GitHub Desktop  
**技术环境：** Python 3.12 + uv + FastAPI + pytest + Ruff

## 一、核心原则

团队使用 GitHub 共享项目代码和依赖配置，每位成员在自己的电脑上维护独立的 Python 虚拟环境。

需要记住以下四条规则：

1. **GitHub 不存储每个人的 Python 虚拟环境。** `.venv/` 只保存在本地，不提交到仓库。
2. **新增或修改项目依赖，必须同时提交 `pyproject.toml` 和 `uv.lock`。** 不能只在本地安装依赖。
3. **拉取其他成员已合并的依赖更新后，必须执行 `uv sync --locked --dev`。** Git Pull 不会自动将新库安装到本地虚拟环境。
4. **功能代码及其测试一起提交 PR。** GitHub Actions 自动验证代码和依赖，但不会自动把依赖安装到其他成员的电脑。

---

## 二、项目中与开发环境有关的文件

| 文件或目录 | 功能 | 是否提交 GitHub |
|---|---|---|
| `pyproject.toml` | 声明项目依赖和工具配置 | 是 |
| `uv.lock` | 锁定依赖解析结果 | 是 |
| `.python-version` | 约定 Python 版本 | 是 |
| `.venv/` | 本地 Python 虚拟环境 | **否** |
| `.github/workflows/ci.yml` | 配置 GitHub 自动检查 | 是 |
| `.gitignore` | 规定不应提交的本地文件 | 是 |
| `backend/` | 后端功能实现和模块测试 | 是 |

其中，最需要关注的是：

**`pyproject.toml` + `uv.lock` + `.venv/`**

前两个文件描述团队应该使用什么依赖，最后一个目录存放当前电脑实际安装的依赖。

---

## 三、新组员第一次加入项目

### 第一步：准备本地工具

确保已安装：

- GitHub Desktop
- VS Code
- uv

打开 VS Code，在项目根目录执行：

```powershell
uv --version
```

如果提示找不到 uv，需要先按照项目 README 安装团队约定版本的 uv。

### 第二步：克隆 GitHub 仓库

使用 GitHub Desktop：

`File → Clone repository`

选择团队仓库，并指定本地目录。

克隆完成后，选择 `Repository → Open in Visual Studio Code`。

### 第三步：安装项目 Python 环境

在 VS Code 终端中，确保当前目录是仓库根目录，然后执行：

```powershell
uv python install
uv sync --locked --dev
```

第一条命令根据 `.python-version` 准备 Python。

第二条命令根据项目配置和锁文件：

- 创建或更新根目录的 `.venv`。
- 安装 FastAPI 等运行依赖。
- 安装 pytest、Ruff 等开发依赖。
- 校验锁文件与依赖声明是否一致。

**不需要手动创建 `.venv`，也不需要复制其他成员的虚拟环境。**

### 第四步：验证环境

```powershell
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

三项检查全部通过，说明本地基础环境已经准备好。

注意：这些命令验证的是当前项目基础检查，并不意味着将来所有数据库、外部服务或部署环境都已经准备好。

---

## 四、开发者新增功能时的操作流程

假设 M1 组员要开发座位预约功能，需要新增 SQLAlchemy 依赖。

### 第一步：同步最新代码并创建功能分支

在 GitHub Desktop：

1. 确认没有未处理的本地修改。
2. 切换到 `main`。
3. 点击 `Fetch origin`，如有更新则 `Pull origin`。
4. 从最新 `main` 创建功能分支。

例如：

`feat/M1-003-seat-reservation`

**禁止直接在 main 上开发业务功能。**

### 第二步：同步当前项目环境

在 VS Code 项目根目录执行：

```powershell
uv sync --locked --dev
```

这一步确保开始开发时，本地环境与当前分支的依赖配置一致。

### 第三步：新增项目依赖

如果需要 SQLAlchemy，执行：

```powershell
uv add sqlalchemy
```

uv 通常会自动完成：

- 修改 `pyproject.toml`。
- 更新 `uv.lock`。
- 将新依赖安装到当前 `.venv`。

如果新增的是仅用于测试或代码检查的开发工具，例如 pytest-cov：

```powershell
uv add --dev pytest-cov
```

**不要仅通过 `pip install` 增加项目依赖，否则依赖可能只存在于个人电脑中。**

如果需要删除依赖，应使用：

```powershell
uv remove sqlalchemy
```

### 第四步：编写功能代码及对应测试

例如：

```text
backend/
└── modules/
    └── m1/
        ├── reservation.py
        └── tests/
            └── test_reservation.py
```

新增功能时，应同步增加能够验证其行为的测试。

### 第五步：本地执行检查

开发完成后执行：

```powershell
uv sync --locked --dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

只有所有适用检查通过，才应提交 PR。

如果某项检查失败，需要先排查。不得简单删除测试或屏蔽错误来获得通过结果。

### 第六步：使用 GitHub Desktop 提交

在 GitHub Desktop 的 `Changes` 页面检查文件。

如果新增了依赖，本次提交应当包含：

```text
backend/modules/m1/reservation.py
backend/modules/m1/tests/test_reservation.py
pyproject.toml
uv.lock
```

不要提交：

```text
.venv/
__pycache__/
.env
个人密钥或本地缓存
```

填写 Commit 信息并提交，然后点击 `Push origin` 或 `Publish branch`。

### 第七步：创建 PR

在 GitHub 上创建指向 `main` 的 Pull Request。

PR 描述应说明：

- 新增了什么功能。
- 新增或修改了哪些依赖。
- 增加了哪些测试。
- 本地验证结果。
- 是否涉及跨模块接口或数据库结构变化。

随后 GitHub Actions 将自动执行 CI。

CI 通过并经其他成员人工审核后，才能按照团队约定合并。

---

## 五、其他组员如何同步最新代码和依赖？

这是所有成员需要重复执行的流程。

假设 M1 组员已经把新增 SQLAlchemy 的 PR 合并进 `main`。

### 情况 A：准备开始新的开发任务

**第一步：Pull 最新 main**

打开 GitHub Desktop：

1. 切换到 `main`。
2. 点击 `Fetch origin`。
3. 有远程更新时，点击 `Pull origin`。

Git 会将最新的 `pyproject.toml`、`uv.lock` 以及业务代码下载到本地。

**第二步：同步 Python 环境**

在 VS Code 项目根目录执行：

```powershell
uv sync --locked --dev
```

uv 会根据新的依赖配置调整 `.venv`：

- 安装新增依赖。
- 根据锁文件更新需要更新的依赖。
- 移除不再需要的受管理依赖。

**第三步：运行检查**

```powershell
uv run --locked pytest
```

建议同时运行 Ruff 检查，确保当前开发环境能够正常工作。

**第四步：从最新 main 创建新的任务分支。**

此时就可以继续开发了。

### 情况 B：已经在自己的功能分支开发，别人更新了 main

例如你正在开发 M2，而 M1 的新依赖已经合并进 `main`。

此时不建议直接切换到 main 后就忘记了自己正在开发的分支。

推荐流程：

1. 先保存或提交当前功能分支中的工作，避免丢失未提交修改。
2. 在 GitHub Desktop 中切换到 `main`。
3. Fetch/Pull 最新 `main`。
4. 切换回自己的 M2 功能分支。
5. 使用 GitHub Desktop 的分支更新功能，将最新 `main` 合并到当前功能分支，或按团队约定使用 Rebase。
6. 如有合并冲突，由组员人工判断并解决。
7. 在当前功能分支执行：

```powershell
uv sync --locked --dev
uv run --locked pytest
```

注意：**仅更新本地 main，不代表正在开发的功能分支也已经获得 main 的新提交。** 需要进行第 5 步。

如果两个分支同时修改过 `pyproject.toml` 或 `uv.lock`，可能产生冲突。不要直接保留某一方的旧锁文件而忽略另一方新增的依赖，应先人工确认依赖声明，再通过 uv 重新解析和生成一致的锁文件，并进行测试。
---



## 下一步与待决事项

1. 确认分工、D 归属、契约维护者及发布协调人，评审暂定 [ADR-0001](docs/adr/0001-repository-boundaries.md)。
2. 完善需求与可执行验收标准，讨论其他集成点，确定优先级和迭代安排。
3. 确认网络拓扑、数据所有权/隔离、占用冲突及一致性/重试/补偿方案。
4. 人工验收基础环境与 CI，核实 GitHub 双平台结果和保护设置；继续选择迁移工具、云资源、环境与凭据管理方案。
5. 逐步实现服务与真实验证、迁移和流水线，持续维护需求、决策、伦理和发布证据。
6. 主线成熟后评估 DSH 插件、代理意图澄清与写操作确认、安装及交付方案。
