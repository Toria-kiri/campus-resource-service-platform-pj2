# M3 物业报修工单模块接口文档 V0.1

- 项目名称：校园资源服务平台
- 模块：M3 — 物业报修工单
- 版本：V0.1（设计草案，与 M3 需求评审稿 V0.1 §7.1 对齐）
- 状态：**尚未实现**。当前仓库仅有 `GET /health`；本文所有业务接口均为待实现的设计约定
- 日期：2026-10-25
- 建议存放位置：`contracts/m3.md`（与 `contracts/health.md` 同级）

> 本文中的路径、字段、错误码继承自 M3 需求评审稿 §7 的建议；标注 **†** 的条目是本文新增的建议，需团队评审确认。鉴权头、错误响应体、分页格式等待团队统一格式确定后替换本文的临时约定。

---

## 1. 通用约定

### 1.1 基础信息

| 项 | 约定 |
| --- | --- |
| Base URL | `/api/m3` |
| 传输格式 | JSON（UTF-8），请求头 `Content-Type: application/json` |
| 鉴权 | 所有接口须登录。建议 `Authorization: Bearer <token>`，具体方案随 D 统一鉴权契约（待对齐） |
| 身份来源 | 操作者身份一律取自 D 的可信认证上下文；请求体中的 `reporterId`、`operatorId` 等身份字段**不被信任**，仅作展示回显 |
| 时间 | 服务端时间、校园时区 `Asia/Shanghai`；时间戳采用带偏移的 ISO 8601，如 `2026-10-25T14:30:00+08:00` |
| 区间语义 | 停用等时间区间为左闭右开 `[start, end)`；仅当 `start1 < end2 && start2 < end1` 时视为重叠 |

### 1.2 权限标识

| 权限 | 适用接口 |
| --- | --- |
| `M3_REPORT` | 教室列表、创建报修、本人记录、合法取消、完成后评价 |
| `M3_DISPATCH` | 评估、驳回、派单/改派、任务查询（调度范围） |
| `M3_WORK` | 开始维修、追加进度、提交完工（限当前分配给本人的工单） |
| `M3_ACCEPT` | 验收通过/退回（限授权范围，且满足验收隔离） |
| `M3_RESOURCE_CONTROL` | 资源影响确认与变更、安全恢复 |

无权限返回 `403 FORBIDDEN`；对无权读取的工单统一返回 `404 NOT_FOUND`，不泄露工单存在性。

### 1.3 幂等（对应需求 R05）

- 所有 `POST` 写操作必须携带请求头 `Idempotency-Key: <uuid>`。
- 服务端按「认证用户 + 操作类型 + 目标工单 + 幂等键」绑定请求内容；创建操作以「用户 + 操作类型=创建」为范围。
- 同键同内容：返回已有结果；若原请求仍在处理中（如等待 D 确认），返回相同的处理中响应与 `operationId`。
- 同键不同内容：返回 `409 IDEMPOTENCY_CONFLICT`，不覆盖原请求。
- **结果未知（`202`）时不得换新幂等键重试**，应使用相同键重发或轮询详情接口。

### 1.4 分页 †（临时约定，待与团队格式对齐）

- 请求参数：`page`（从 1 起，默认 1）、`pageSize`（默认 20，最大 100）。
- 响应结构：`{ "items": [...], "page": 1, "pageSize": 20, "total": 123 }`。

### 1.5 状态码与错误响应 †（临时约定，待对齐）

| HTTP | 使用场景 |
| --- | --- |
| 200 | 成功 |
| 201 † | 创建报修成功 |
| 202 | 操作已受理但结果未知（限制建立/解除等待 D 确认）；响应含 `operationId`，不是错误 |
| 400 | 参数校验失败 |
| 401 | 未登录 |
| 403 | 无权限或违反验收隔离 |
| 404 | 资源不存在，或对无权读取的工单隐藏存在性 |
| 409 | 状态冲突、幂等冲突、计划限制冲突 |
| 502 / 503 | 依赖（D）不可达或明确失败 |

错误响应体（临时约定）：

```json
{
  "error": {
    "code": "STATE_CONFLICT",
    "message": "工单当前状态不允许该操作",
    "requestId": "req-8f3a2b"
  }
}
```

错误码全集及映射见 §5。

### 1.6 枚举定义

| 枚举 | 取值 |
| --- | --- |
| `category` 故障类别 | `ELECTRICAL` 电气 / `LIGHTING` 照明 / `FURNITURE` 家具 / `ENVIRONMENT` 环境 / `OTHER` 其他 |
| `urgency` 处理紧急度 | `NORMAL` / `URGENT` |
| `impactType` 资源影响 | `UNASSESSED` 未确认 / `NOTICE_ONLY` 仅提示 / `PLANNED_STOP` 计划停用 / `EMERGENCY_STOP` 紧急停用 |
| `status` 工单状态 | `SUBMITTED` / `ASSIGNED` / `IN_PROGRESS` / `PENDING_ACCEPTANCE` / `COMPLETED` / `REJECTED` / `CANCELLED` |
| `syncState` 限制同步状态 | `NONE` / `CREATE_PENDING` / `ACTIVE` / `RELEASE_PENDING` / `RELEASED` / `CREATE_REJECTED` |

---

## 2. 接口总览

| # | 方法 | 路径 | 功能 | 权限 | 幂等键 | 建议批次 † |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | GET | `/api/m3/classrooms` | 可报修教室列表 | `M3_REPORT` | — | P0 |
| 2 | POST | `/api/m3/work-orders` | 提交报修 | `M3_REPORT` | 必填 | P0 |
| 3 | GET | `/api/m3/work-orders/my` | 本人报修记录 | 登录 + 归属 | — | P0 |
| 4 | GET | `/api/m3/work-orders/{id}` | 工单详情 | 归属/分配/管理范围 | — | P0 |
| 5 | POST | `/api/m3/work-orders/{id}/cancel` | 报修人取消 | 本人 + 条件 | 必填 | P0 |
| 6 | GET | `/api/m3/tasks` | 按角色返回任务列表 | 按角色 | — | P0 |
| 7 | POST | `/api/m3/work-orders/{id}/assessment` | 有效性/紧急度评估 | `M3_DISPATCH` | 必填 | P0 |
| 8 | POST | `/api/m3/work-orders/{id}/reject` | 无效报修驳回 | `M3_DISPATCH` | 必填 | P0 |
| 9 | POST | `/api/m3/work-orders/{id}/assignments` | 派单/改派 | `M3_DISPATCH` | 必填 | P0 |
| 10 | POST | `/api/m3/work-orders/{id}/start` | 开始维修 | 当前维修人 | 必填 | P0 |
| 11 | POST | `/api/m3/work-orders/{id}/progress` | 追加进度 | 当前维修人 | 必填 | P0 |
| 12 | POST | `/api/m3/work-orders/{id}/finish` | 提交完工 | 当前维修人 | 必填 | P0 |
| 13 | POST | `/api/m3/work-orders/{id}/acceptance` | 验收通过/退回 | `M3_ACCEPT` + 隔离 | 必填 | P0 |
| 14 | POST | `/api/m3/work-orders/{id}/resource-impact` | 确认/变更资源影响 | `M3_RESOURCE_CONTROL` | 必填 | P0（仅 `NOTICE_ONLY`/`EMERGENCY_STOP`）/ P1（`PLANNED_STOP`） |
| 15 | POST | `/api/m3/work-orders/{id}/recovery` | 安全恢复并解除 | `M3_RESOURCE_CONTROL` | 必填 | P0 |
| 16 | POST | `/api/m3/work-orders/{id}/evaluation` | 完成后评价 | 本人 | 必填 | P0 |

「建议批次」对应需求稿评审意见中的分层：P0 = 首迭代单模块闭环 + 紧急停用最小联动；P1 依赖 D 的计划限制契约。仅作评审建议，最终以团队结论为准。

---

## 3. 接口详细说明

### 3.1 可报修教室列表

`GET /api/m3/classrooms` · 权限 `M3_REPORT`

返回当前用户**有权报修**的教室，含长期禁用教室（禁用不等于不可报修）。

**响应 200**

```json
{
  "items": [
    { "roomId": "ROOM-101", "name": "一号楼 101", "location": "一号楼 1 层", "seatCount": 120, "disabled": false },
    { "roomId": "ROOM-202", "name": "二号楼 202", "location": "二号楼 2 层", "seatCount": 80, "disabled": true }
  ]
}
```

**错误**：`401`；D 不可达 → `502/503 DEPENDENCY_UNAVAILABLE`（不伪造教室数据）。

---

### 3.2 提交报修

`POST /api/m3/work-orders` · 权限 `M3_REPORT` · 幂等必填

**请求体**（字段规则对应需求 R04）

| 字段 | 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `roomId` | string | 是 | 教室存在且当前用户可报修，从 D 核验 |
| `seatId` | string | 否 | 若填写必须属于该教室；仅用于故障定位，不产生座位级阻断 |
| `category` | enum | 是 | 见 §1.6 |
| `title` | string | 是 | 去首尾空白后 5～80 字符 |
| `description` | string | 是 | 去首尾空白后 10～1000 字符 |
| `suspectedSafetyIssue` | boolean | 否 | 默认 `false`；是用户提供的线索，**不构成停用授权** |

```json
{
  "roomId": "ROOM-101",
  "seatId": "SEAT-101-05",
  "category": "LIGHTING",
  "title": "教室后排照明持续闪烁",
  "description": "后排靠窗位置的照明持续闪烁，影响阅读，请安排检查。",
  "suspectedSafetyIssue": false
}
```

**响应 201 †**

```json
{
  "workOrderId": "WO-000001",
  "workOrderNo": "M3-20261025-0001",
  "status": "SUBMITTED",
  "urgency": "NORMAL",
  "impactType": "UNASSESSED",
  "createdAt": "2026-10-25T14:30:00+08:00"
}
```

勾选疑似安全问题时创建后 `urgency = URGENT`，进入待评估优先队列；不赋予报修人任何停用权限。

**错误**：`400 INVALID_REPORT`（字段越界、类别非法、教室/座位不匹配）；`403 FORBIDDEN`（无该教室报产权）；`409 IDEMPOTENCY_CONFLICT`；`502/503 DEPENDENCY_UNAVAILABLE`。

---

### 3.3 本人报修记录

`GET /api/m3/work-orders/my` · 登录 + 归属

**查询参数**：`page`、`pageSize`；`dateFrom`/`dateTo`（ISO 日期）、`roomId`、`status`（可选筛选）。

**响应 200**：`items` 为工单摘要数组（结构见 §4.1），另含当前用户可见的 `cancelable`、`evaluable †`（可评价）等操作提示布尔值（仅提示用，后端独立校验）。

**错误**：`401`；查询失败返回明确错误，不得以空列表冒充。

---

### 3.4 工单详情

`GET /api/m3/work-orders/{id}` · 归属/当前分配/管理范围

可见角色：报修人、当前维修人（及本轮参与人员履职必需的历史）、授权调度/验收/资源管理人员。无权访问一律 `404`，不泄露存在性。

**响应 200**：完整结构见 §4.2。要点：

- `resourceImpacts` 按来源逐条返回同步状态；`CREATE_PENDING`/`RELEASE_PENDING` 时前端展示「停用同步中/恢复同步中」，不得展示为已生效。
- `actions` 为脱敏后的操作时间线（类型、角色、时间、公开内容）；完整故障描述、评价、内部意见按 §R03 范围过滤。

**错误**：`401`；`404 NOT_FOUND`。

---

### 3.5 报修人取消

`POST /api/m3/work-orders/{id}/cancel` · 本人 · 幂等必填

**前置条件（R11）**：状态为 `SUBMITTED`、尚未派单、无已确认停用要求、不存在生效或在途限制。已派单/维修中/待验收一律拒绝。

**请求体**：`{ "reason": "5～500 字符，必填 †" }`

**响应 200**：`{ "status": "CANCELLED", "cancelledAt": "...", "reason": "..." }`。不解除任何其他来源的限制。

**错误**：`403`（非本人）；`404`；`409 STATE_CONFLICT`（已派单或存在停用要求/在途限制）；`409 IDEMPOTENCY_CONFLICT`。

---

### 3.6 任务列表

`GET /api/m3/tasks` · 按调用者角色返回

**查询参数**：`scope †`（`repair`/`dispatch`/`acceptance`，缺省按调用者全部角色合并）；`status`、`roomId`、`impactType`、`suspectedSafetyOnly`、`overdueOnly †`（仅超时升级）、`page`、`pageSize`。

**响应 200**：`items` 为工单摘要 + 角色相对信息：

```json
{
  "items": [
    {
      "workOrderId": "WO-000003",
      "workOrderNo": "M3-20261025-0003",
      "roomId": "ROOM-101", "roomName": "一号楼 101", "seatId": null,
      "category": "ELECTRICAL", "title": "插座冒火花",
      "status": "SUBMITTED", "urgency": "URGENT", "impactType": "UNASSESSED",
      "suspectedSafetyIssue": true,
      "currentAssignee": null,
      "createdAt": "2026-10-25T14:00:00+08:00",
      "stageDeadlineAt": "2026-10-25T14:15:00+08:00",
      "escalated": false
    }
  ],
  "page": 1, "pageSize": 20, "total": 1
}
```

`stageDeadlineAt` 为当前阶段截止（R14）；`escalated` 表示已存在未处理的超时升级记录。调度范围须同时暴露「限制同步失败/待处理」条目，避免仅按工单状态筛选漏掉安全操作。

**错误**：`401`；`403`。

---

### 3.7 评估

`POST /api/m3/work-orders/{id}/assessment` · `M3_DISPATCH` · 幂等必填

**请求体** †

| 字段 | 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `urgency` | enum | 是 | `NORMAL` / `URGENT` |
| `comment` | string | 否 | 0～500 字符 |
| `isAdjustment` | boolean | 否 | 默认 `false`；首次评估后调整紧急度时置 `true`，追加留痕，不覆盖原记录 |

**响应 200**：更新后的工单摘要。工单状态保持 `SUBMITTED`，直至派单。

**错误**：`400 INVALID_ARGUMENT †`；`403`；`404`；`409 ALREADY_EVALUATED`（已评估且未声明为调整）；`409 IDEMPOTENCY_CONFLICT`。

注：评估为「有效性 + 紧急度」确认；判定报修无效走 §3.8 驳回。确认 `EMERGENCY_STOP` 属资源影响确认，走 §3.13，仅有调度权限不得执行。

---

### 3.8 驳回

`POST /api/m3/work-orders/{id}/reject` · `M3_DISPATCH` · 幂等必填

**前置条件（R11）**：尚未派单、无已确认停用要求、无生效/在途限制。

**请求体** †：`{ "reason": "5～500 字符，必填", "duplicateOfWorkOrderId": "可选，重复报修时关联的原工单" }`（关联不删除、不合并任何记录）。

**响应 200**：`{ "status": "REJECTED", "rejectedAt": "...", "reason": "..." }`

**错误**：`403`；`404`；`409 STATE_CONFLICT`；`409 IDEMPOTENCY_CONFLICT`。

---

### 3.9 派单 / 改派

`POST /api/m3/work-orders/{id}/assignments` · `M3_DISPATCH` · 幂等必填

**请求体** †

| 字段 | 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `assigneeId` | string | 是 | 须为 D 中当前有效、具有维修资格且覆盖目标教室的人员 |
| `reason` | string | 否 | 0～500 字符 |
| `handoverNote` | string | 条件 | `IN_PROGRESS` 改派时必填，5～500 字符 |

**行为（R07）**：`SUBMITTED → ASSIGNED`；`ASSIGNED` 改派状态不变；`IN_PROGRESS` 改派状态仍为维修中，旧处理人立即失去写权限，已提交记录保留。并发派单只能形成一个有效当前分配。

**响应 200**：`{ "status": "ASSIGNED" | "IN_PROGRESS", "currentAssignee": {...}, "assignedAt": "...", "reassigned": true }`

**错误**：`400 INVALID_ASSIGNEE`（人员失效/无资格/不覆盖本教室）；`403`；`404`；`409 STATE_CONFLICT`；`409 IDEMPOTENCY_CONFLICT`。

---

### 3.10 开始维修

`POST /api/m3/work-orders/{id}/start` · 当前维修人 · 幂等必填

**请求体**：`{}`（无参数，实际开始时间取服务端时间）

**前置条件（R08）**：状态 `ASSIGNED` 且操作者为当前维修人。需停用的施工：须 D 已确认相应限制生效；计划施工另须到达获准开始时刻。

**响应 200**：`{ "status": "IN_PROGRESS", "startedAt": "..." }`。开始普通维修**不**自动创建任何停用。

**错误**：`403`（非当前维修人）；`404`；`409 STATE_CONFLICT`（含未到获准施工窗口）；`409 RESTRICTION_NOT_CONFIRMED`（限制未生效即开工）；`409 IDEMPOTENCY_CONFLICT`。

---

### 3.11 追加进度

`POST /api/m3/work-orders/{id}/progress` · 当前维修人 · 幂等必填

**请求体**：`{ "content": "1～1000 字符，必填" }`

**响应 200**：`{ "progressId": "...", "at": "..." }`。仅追加，不能修改他人已提交内容。进度更新不重置任何阶段截止。

**错误**：`400 INVALID_ARGUMENT`；`403`；`404`；`409 STATE_CONFLICT`（非 `IN_PROGRESS`）；`409 IDEMPOTENCY_CONFLICT`。

---

### 3.12 提交完工

`POST /api/m3/work-orders/{id}/finish` · 当前维修人 · 幂等必填

**请求体**：`{ "result": "5～1000 字符，必填" }`

**响应 200**：`{ "status": "PENDING_ACCEPTANCE", "finishedAt": "..." }`。不自动验收、不解除停用。同键重试返回既有结果，一轮仅一条有效完工。

**错误**：`400 INVALID_ARGUMENT`；`403`；`404`；`409 STATE_CONFLICT`（未开始即完工、改派并发等按串行状态校验裁决）；`409 IDEMPOTENCY_CONFLICT`。

---

### 3.13 资源影响确认与变更

`POST /api/m3/work-orders/{id}/resource-impact` · `M3_RESOURCE_CONTROL` · 幂等必填

**请求体** †

| 字段 | 类型 | 必填 | 规则 |
| --- | --- | --- | --- |
| `impact` | enum | 是 | `NOTICE_ONLY` / `PLANNED_STOP` / `EMERGENCY_STOP`（`UNASSESSED` 为初始态，不可主动设置） |
| `reason` | string | 是 | 5～500 字符，留痕 |
| `stopFrom` / `stopTo` | string | 条件 | 仅 `PLANNED_STOP` 必填；须为未来区间且 `stopFrom < stopTo`；紧急停用**不接受**前端指定生效时间，以服务端确认时刻为准 |

**响应（按结果分三种）**

1. `NOTICE_ONLY` → `200`，`{ "impactType": "NOTICE_ONLY", "syncState": "NONE" }`：仅发布脱敏提示，不建立阻断限制。
2. `PLANNED_STOP` → D 原子冲突检查通过：`200`，`syncState = ACTIVE`（是否到生效时刻按区间另判）；与既有 M1/M2 占用冲突被拒：`409 PLAN_CONFLICT`，该来源记 `CREATE_REJECTED`，不建立限制、不取消任何预约；D 不可达/超时：`202`（见下）。
3. `EMERGENCY_STOP` → D 快速确认：`200`，`syncState = ACTIVE`，含可信生效时刻；结果未知：`202`。

**202 响应体** †

```json
{
  "operationId": "OP-000042",
  "status": "RESULT_PENDING",
  "syncState": "CREATE_PENDING",
  "message": "已受理，等待资源服务确认；请轮询工单详情，勿更换幂等键重试"
}
```

**错误**：`400 INVALID_ARGUMENT`；`403`（含仅有调度权限试图确认停用）；`404`；`409 PLAN_CONFLICT`；`409 IDEMPOTENCY_CONFLICT`；`502/503 DEPENDENCY_UNAVAILABLE`。

注：紧急停用被 D 明确拒绝时的处理（按同步异常进入待处理并人工介入，不得静默放弃阻断）需求稿未定义，本文暂按 `202` + `CREATE_PENDING` 持续核实处理，**待需求评审补充**。

---

### 3.14 安全恢复

`POST /api/m3/work-orders/{id}/recovery` · `M3_RESOURCE_CONTROL` · 幂等必填

**前置条件（R20）**：涉及停用的工单须已通过独立技术验收；未验收即申请恢复 → `409 RECOVERY_NOT_CONFIRMED`。维修人员完工或报修人评价不能替代本操作。

**请求体** †：`{ "note": "5～500 字符，必填（安全恢复依据）" }`

**行为**：按本工单每个已建立的限制来源向 D 请求解除；只解除本来源，其他工单限制、M1/M2 占用、长期禁用不受影响。

**响应**：`200`（全部来源 `RELEASED`，工单可进入 `COMPLETED`）或 `202`（`RELEASE_PENDING` + `operationId`，继续轮询，不提前显示完成）。

**错误**：`403`；`404`；`409 RECOVERY_NOT_CONFIRMED`；`409 STATE_CONFLICT`（无有效限制）；`409 IDEMPOTENCY_CONFLICT`；`502/503 DEPENDENCY_UNAVAILABLE`。

---

### 3.15 完成后评价

`POST /api/m3/work-orders/{id}/evaluation` · 本人（报修人）· 幂等必填

**前置条件（R12）**：工单 `COMPLETED`；每工单仅一条。

**请求体**：`{ "score": 1～5 整数，必填", "comment": "0～500 字符，可选" }`

**响应 200**：`{ "evaluationId": "...", "score": 4, "at": "..." }`。评价不改变工单、验收或资源状态。

**错误**：`400 INVALID_ARGUMENT`（0/6/小数等）；`404`（含非本人工单，统一不泄露存在性）；`409 STATE_CONFLICT`（未完成）；`409 IDEMPOTENCY_CONFLICT`（不同键重复评价）；同键同内容重试返回原评价。

---

### 3.16 健康检查

见 `contracts/health.md`，本文不重复。

---

## 4. 数据结构

### 4.1 工单摘要（列表项）†

```json
{
  "workOrderId": "WO-000001",
  "workOrderNo": "M3-20261025-0001",
  "roomId": "ROOM-101", "roomName": "一号楼 101", "seatId": "SEAT-101-05",
  "category": "LIGHTING", "title": "教室后排照明持续闪烁",
  "status": "SUBMITTED", "urgency": "NORMAL", "impactType": "UNASSESSED",
  "suspectedSafetyIssue": false,
  "currentAssignee": { "userId": "U-77", "name": "王师傅" },
  "createdAt": "2026-10-25T14:30:00+08:00",
  "stageDeadlineAt": "2026-10-25T16:30:00+08:00",
  "escalated": false
}
```

### 4.2 工单详情 †

摘要字段之外，另含：

```json
{
  "description": "……（按 R03 范围过滤）",
  "round": 1,
  "times": {
    "assignedAt": null, "startedAt": null, "finishedAt": null,
    "acceptedAt": null, "completedAt": null,
    "cancelledAt": null, "rejectedAt": null
  },
  "cancelOrRejectReason": null,
  "resourceImpacts": [
    {
      "sourceId": "RS-000009",
      "impactType": "EMERGENCY_STOP",
      "version": 1,
      "interval": { "stopFrom": "2026-10-25T15:00:00+08:00", "stopTo": null },
      "syncState": "ACTIVE",
      "confirmedBy": { "userId": "U-05" },
      "confirmedAt": "2026-10-25T15:00:00+08:00"
    }
  ],
  "actions": [
    { "type": "CREATED", "at": "2026-10-25T14:30:00+08:00", "actorRole": "REPORTER" },
    { "type": "PROGRESS", "at": "2026-10-25T16:00:00+08:00", "actorRole": "REPAIRER", "content": "已更换镇流器（公开摘要）" }
  ],
  "evaluation": null
}
```

`interval.stopTo = null` 表示开放结束的持续限制。`actions` 与 `evaluation` 按调用者角色脱敏返回。

---

## 5. 错误码映射

| 错误码 | HTTP | 语义 |
| --- | --- | --- |
| `UNAUTHORIZED` | 401 | 未登录 |
| `FORBIDDEN` | 403 | 无权限、范围外操作、违反验收隔离 |
| `NOT_FOUND` | 404 | 不存在或对无权者隐藏存在性 |
| `INVALID_REPORT` | 400 | 报修创建字段/教室/座位校验失败 |
| `INVALID_ARGUMENT †` | 400 | 其余接口的参数校验失败 |
| `STATE_CONFLICT` | 409 | 状态不允许、前置条件不满足（除下列专码外） |
| `INVALID_ASSIGNEE` | 400 | 派单对象失效/无资格/不覆盖教室 |
| `SELF_ACCEPTANCE_FORBIDDEN` | 403 | 本轮维修参与人验收本轮 |
| `PLAN_CONFLICT` | 409 | 计划限制与既有 M1/M2 占用冲突，被 D 拒绝 |
| `RESTRICTION_NOT_CONFIRMED` | 409 | 限制未生效即尝试开工 |
| `RECOVERY_NOT_CONFIRMED` | 409 | 未经独立验收即尝试恢复 |
| `ALREADY_EVALUATED` | 409 | 重复首次评估且未声明为调整 |
| `IDEMPOTENCY_CONFLICT` | 409 | 同键不同内容 |
| `DEPENDENCY_UNAVAILABLE` | 502/503 | D 不可达或明确失败，不伪造结果 |

`RESULT_PENDING` 不是错误码，仅出现在 `202` 响应体中表示结果未知。

---

## 6. 接口与需求规则追踪

| 接口 | 对应需求 | 主要验收编号 |
| --- | --- | --- |
| 3.1 / 3.2 | R01、R04、F01 | T01–T07、T44 |
| 3.3 / 3.4 | R01、R03、F02 | T02、T44 |
| 3.5 | R11 | T19、T20 |
| 3.6 | R15、F03/F04/F05 | T23–T25 |
| 3.7 / 3.8 | R06、R11 | T07、T19、T20 |
| 3.9 | R07 | T09–T11 |
| 3.10 / 3.11 / 3.12 | R08、R09 | T12–T14、T29 |
| 3.13 | R10 | T15–T18 |
| 3.14（resource-impact） | R06、R16–R18 | T26–T28、T30、T31 |
| 3.15（recovery） | R20 | T36–T38、T49 |
| 3.16（evaluation） | R12 | T21、T22 |

---

## 7. 待团队确认事项

1. 统一鉴权头、错误响应体、分页格式（§1.4/§1.5 为临时约定）与 D/其他模块对齐后替换。
2. 创建成功返回 `201` 还是统一 `200`；工单编号 `workOrderNo` 的生成格式。
3. 评估调整机制（`isAdjustment`）与 `ALREADY_EVALUATED` 的边界是否符合 R06 预期。
4. 紧急停用被 D **明确拒绝**（而非超时）时的处理路径，需求稿 R18/5.2 未定义。
5. `PLANNED_STOP` 依赖 D 的计划限制与到期协调契约（需求稿 §7.2），契约冻结前该分支标记为依赖未就绪。
6. `202` 的通知方式（轮询详情 vs D 回调）与回调鉴权，随跨模块契约共同评审。

本文为设计草案，所有接口尚未实现；实现后须逐条补充真实请求/响应示例与测试证据。
