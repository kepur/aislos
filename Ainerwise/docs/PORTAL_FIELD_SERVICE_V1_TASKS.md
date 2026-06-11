# AinerWise Portal & Field Service V1 Tasks

更新日期：2026-06-11

主实现仓库：`/Users/mac/Code_Start/Aislos/Ainerwise`

共享平台规划：`/Users/mac/Code_Start/Aislos/SHARED_PLATFORM_MIDDLEWARE_PLAN.md`

---

## 0. 冻结结论

> **One physical frontend family does not mean one interface.**

中文解释：

> 只维护三套前端代码基座，但 Customer、Partner Company、Field Worker、Supplier、Kiosk 必须拥有不同布局、菜单、路由、权限和任务流程。

冻结规则：

1. 物理前端代码基座永远最多三套：
   - `frontend-pc`
   - `frontend-h5`
   - `frontend-admin`
2. Logical Portal 由 `Portal Manifest + Membership + Grant + Route Allowlist + Theme + Menu` 生成。
3. 一个账号可以拥有多个 Membership，登录后只能选择自己被授权的工作空间。
4. Partner Company 与 Field Worker 绝不是同一个界面。
5. 电工、安装工、KNX 调试员、安防工程师、维护人员不各建一个 App；它们是 Field Worker PWA 中不同的任务类型、技能和证书。
6. 后台不拆成十几个工程；一个 `frontend-admin` 根据 Grant 显示十几个业务工作台。
7. Worker 是任务驱动，不是固定角色驱动。
8. `MaintenanceSchedule` 只代表维保计划，不再作为所有施工任务模型。

---

## 1. 当前真实状态

### 1.1 当前运行入口

#### PC

| Portal | 地址 | 当前状态 |
|---|---|---|
| AISLOS Website | `http://localhost:4099` | 已有 |
| Store | `http://localhost:4096` | 已有 |
| Developer | `http://localhost:4092` | 已有 |
| Nginx AISLOS | `http://localhost` | 已有 |
| Nginx Cebu | `http://cebu.localhost` | 已有，采购双品牌临时入口 |

#### H5

| Portal | 地址 | 当前状态 |
|---|---|---|
| Customer | `http://localhost:4098` | 已有 |
| Partner | `http://localhost:4091` | 已有，但错误混合 Partner Company 与 Worker |
| Kiosk | `http://localhost:4090` | 已有 |

#### Admin

用户列出的 Admin 少了两个当前已有入口：

| Portal | 地址 | 当前状态 |
|---|---|---|
| AISLOS Admin | `http://localhost:4097` | 已有 |
| Store Admin | `http://localhost:4095` | 已有 |
| Marketing | `http://localhost:4094` | 已有 |
| Agent Console / AI Supervisor 基础 | `http://localhost:4093` | 已有 |

### 1.2 当前 H5 缺口

当前 `frontend-h5` 只有：

```text
customer | partner | kiosk
```

当前 `partner` 模式同时接受：

```text
service_partner | partner_worker | maintenance_worker
```

但 Partner API 的 `_partner_for_user()` 又要求每个登录用户直接关联一个 `ServicePartner`。这会导致 Worker 被迫伪装成 Partner Company 主档案，违反目标模型。

当前已有：

- Partner RFQ、报价、日历和简单任务。
- 按 `assigned_to=user.id` 查看任务。
- 手机拍照上传。
- 完工记录、设备序列号、测试结果。
- 客户签署和验收闭环基础。

当前缺失：

- Partner Company 与 Worker 独立界面。
- Workspace / Membership / Portal Grant。
- Partner Company -> Crew -> Worker。
- Worker 跨 Crew 的有效期 Membership。
- WorkPackage / FieldTask / TaskAssignment / Evidence 正式模型。
- Field Operations Admin 调度台。
- Supplier H5。
- 今日任务、导航地址、客户联系权限控制。
- 二维码扫描绑定设备。
- 定位与签到证据。
- 电子签名现场交接。
- IndexedDB、Offline Queue、Service Worker 和幂等同步。
- 按任务动态生成检查清单。

### 1.3 演示账号缺口

当前主要演示账号：

```text
客户：demo@ainerwise.com / demo123
管理员：admin@ainerwise.com / admin123456
```

它们无法覆盖 Portal 与现场权限。PF10 前必须提供可重置的本地测试身份：

```text
customer_owner
customer_member
partner_company_owner
partner_dispatcher
crew_lead
installer_worker
electrician_worker
maintenance_worker
supplier_operator
project_manager
marketing_operator
ai_supervisor
finance_auditor
```

测试身份只用于本地和测试环境；生产环境不得保留固定演示密码。

---

## 2. 最终前端数量

### 2.1 物理代码基座：3

| 代码基座 | 主要用途 |
|---|---|
| `frontend-pc` | AinerWise Consumer Platform、公开采购、开发者和公开页面 |
| `frontend-h5` | Customer、Partner Company、Field Worker、Supplier、Kiosk |
| `frontend-admin` | 内部运营、采购、项目、现场、营销、AI、财务、审计 |

不新增：

- `frontend-worker`
- `frontend-electrician`
- `frontend-installer`
- `frontend-supplier`
- `frontend-partner-company`
- `frontend-field-admin`

### 2.2 H5 逻辑体验：5

| Logical H5 Portal | 用户 | 首页重点 | 明确看不到 |
|---|---|---|---|
| Customer PWA | 客户 Owner / Customer User | 需求、采购、项目、审批、安装计划、验收、资产、售后 | 内部成本、供应商底价、Worker 私有信息 |
| Partner Company PWA | Partner Owner / Dispatcher | RFQ、报价、WorkPackage、Crew、Worker、排期、交付表现 | 其他 Partner、客户非必要数据 |
| Field Worker PWA | 安装工、电工、调试员、维护员、Crew Lead | 今日任务、导航、清单、照片、扫码、定位、签字、完工 | RFQ 报价、利润、公司财务、全量客户资料 |
| Supplier PWA | 设备/材料供应商 | RFQ、报价、目录、订单、发货、质保 | 施工现场内部任务、其他供应商报价 |
| Kiosk PWA | 门店设备/访客 | AI 接待、产品展示、线索收集、店员确认 | 登录后台、客户项目、内部数据 |

### 2.3 Field Worker 不按工种拆 App

以下都使用同一个 Field Worker PWA：

```text
installer
electrician
knx_commissioner
solar_technician
security_technician
network_technician
hvac_technician
maintenance_technician
inspector
delivery_worker
crew_lead
```

差异来自：

- Worker Capability。
- Certification。
- Crew Membership。
- Field Task type。
- Task Checklist Manifest。
- Task Assignment Grant。

### 2.4 Admin 逻辑工作台

一个 `frontend-admin`，至少包含以下权限化工作台：

1. Executive / Operations Dashboard。
2. CRM / Lead。
3. AI Solution / BOQ。
4. Procurement / RFQ / Bid / Award。
5. Supplier Operations。
6. Partner Company / Capability。
7. Field Operations / Dispatch。
8. Project / Acceptance。
9. Asset / Warranty / AMC / Maintenance。
10. Commerce / Order / Payment / Risk。
11. Marketing。
12. AI Supervisor / Agent Console。
13. Knowledge / Living Case。
14. Finance / Margin / Settlement。
15. Audit / Integration / Settings。

用户不应重复登录多个相同后台。登录后根据 Membership 和 Grant 进入所属工作台；未授权菜单和 API 必须同时不可见。

---

## 3. Portal Manifest 契约

每个 Logical Portal 使用版本化 Portal Manifest：

```json
{
  "portal_key": "field_worker",
  "version": 1,
  "layout": "field",
  "home_route": "/field/today",
  "theme_key": "ainerwise-field",
  "menu_keys": ["today", "tasks", "scan", "offline_queue", "profile"],
  "route_allowlist": ["/field/**", "/profile", "/access-denied"],
  "required_grants": ["field_task.read_assigned"],
  "pwa_manifest_key": "field-worker",
  "offline_policy_key": "field-v1"
}
```

规则：

- Portal Manifest 只定义体验，不代替后端权限。
- Browser 不得通过自行提交 `portal_key` 获得权限。
- 后端根据用户 Membership 和 Grant 返回可用 Portal。
- 一个用户可以拥有多个 Portal Membership。
- 切换 Portal 必须记录 Audit Event。
- 所有 API 仍做对象级授权，不能只依赖前端隐藏菜单。

---

## 4. 组织与身份模型

目标层级：

```text
Workspace
  -> Company
    -> Department
      -> Crew
        -> Crew Membership
          -> Field Worker
```

关键规则：

- Partner Company 不是租户本身，而是 Workspace 中的一家公司。
- 一个 Workspace 可以包含多个 Company 和业务部门。
- Worker 不直接永久绑定 Partner Company。
- Worker 可在不同时间属于不同 Crew。
- Crew Lead 是带额外 Grant 的 Worker，不是独立 App。
- 一个用户可同时拥有 Customer、Partner、Supplier 或 Worker Membership。
- 当前单值 `User.role` 暂时保留兼容，最终授权以 Membership + Grant 为准。

建议新增：

```text
workspaces
workspace_memberships
portal_grants
departments
partner_crews
crew_memberships
worker_profiles
worker_capabilities
worker_certifications
```

---

## 5. Field Service 正式模型

冻结业务链：

```text
Project
  -> WorkPackage
    -> Crew
      -> FieldTask
        -> TaskAssignment
          -> TaskEvidence
            -> CustomerAcceptance
              -> Asset
                -> AMC / Maintenance
```

### 5.1 WorkPackage

代表可授标、可交付、可验收的一组工作：

- trade
- scope
- site / zone
- planned dates
- awarded Partner Company
- assigned Crew
- commercial snapshot reference
- status

### 5.2 FieldTask

代表现场人员实际执行的任务：

- work package
- task type
- site / room / zone
- checklist manifest snapshot
- required skill / certification
- schedule window
- safety notes
- status
- offline version

### 5.3 TaskAssignment

- FieldTask 可分配给 Crew 或具体 Worker。
- 每次分配记录有效时间、分配人、原因和状态。
- Worker 只能读取自己当前有效的 Assignment。
- 临时换人必须保留历史记录。

### 5.4 TaskEvidence

Evidence 必须是结构化记录，不只塞进 `completion_json`：

- photo / video
- location
- QR / device serial
- checklist result
- measurement
- test result
- signature
- note
- safety issue
- timestamp
- captured_by
- idempotency key
- sync status

### 5.5 MaintenanceSchedule 边界

- Existing `MaintenanceSchedule` 继续用于周期性维保、校准和更换计划。
- 新施工、安装、交付、调试任务使用 `FieldTask`。
- MaintenanceSchedule 到期后可以生成 FieldTask，但两者不能继续当成同一模型。

---

## 6. Field Worker PWA 必须功能

首版必须支持：

- 今日任务。
- 按时间、距离、优先级排序。
- 地址和一键导航。
- 仅在任务有效期内显示必要客户联系电话。
- 任务范围和施工清单。
- 开工 / 暂停 / 阻塞 / 完工状态。
- 拍照和文件上传。
- 二维码扫描绑定设备。
- 定位签到和证据。
- 测试结果。
- 客户现场签字或发送验收链接。
- Offline Queue。
- IndexedDB 本地缓存。
- Service Worker。
- Idempotency Key。
- 服务端版本冲突检测。
- 断网恢复同步。

离线规则：

- 离线时只缓存已分配给当前 Worker 的最小必要数据。
- 客户电话和敏感数据不得长期离线缓存。
- 每个离线写操作有客户端生成的幂等 Key。
- 同步冲突不能静默覆盖服务端状态。
- Worker 被撤销 Assignment 后，缓存必须过期并清除。

---

## 7. 当前角色到目标 Membership 的迁移

| 当前 `User.role` | 目标 Membership / Grant |
|---|---|
| `buyer` | customer_owner |
| `customer_user` | customer_member |
| `service_partner` | partner_company_owner / dispatcher |
| `partner_worker` | field_worker |
| `maintenance_worker` | field_worker + maintenance grants |
| `vendor` | supplier_company_owner / supplier_operator |
| `project_manager` | field_operations + project_manager |
| `admin` / `super_admin` | admin grants，仍需最小权限 |

迁移要求：

- 不在一次 migration 中删除 `User.role`。
- 先为现有用户幂等创建 Membership。
- API 改为优先检查 Membership + Grant，兼容回退必须有截止日期。
- 完成权限回归后才移除单角色依赖。

---

## 8. 多 Agent 任务控制板

| 完成 | 栏目 | 名称 | 状态 | 依赖 |
|---|---|---|---|---|
| `[x]` | PF00 | Portal 与 Field Service 架构冻结 | `VERIFIED` | 无 |
| `[ ]` | PF01 | Portal Registry、Manifest 与 Route/Grant 契约 | `READY` | PF00 |
| `[ ]` | PF02 | Workspace、Membership 与 Portal Grant | `LOCKED` | PF01 |
| `[ ]` | PF03 | Crew、Worker、WorkPackage、FieldTask 与 Evidence | `LOCKED` | PF02 |
| `[ ]` | PF04 | Field Operations Admin 调度台 | `LOCKED` | PF03 |
| `[ ]` | PF05 | Partner Company H5 | `LOCKED` | PF04 |
| `[ ]` | PF06 | Field Worker PWA 与离线同步 | `LOCKED` | PF05 |
| `[ ]` | PF07 | Supplier H5 | `LOCKED` | PF06 |
| `[ ]` | PF08 | Customer H5 项目交付闭环 | `LOCKED` | PF07 |
| `[ ]` | PF09 | 三物理前端收敛与动态 Manifest | `LOCKED` | PF08 |
| `[ ]` | PF10 | 全角色端到端发布闸门 | `LOCKED` | PF09 |

任何时刻只允许一个 PF 栏目处于 `READY`、`IN_PROGRESS` 或 `READY_FOR_VERIFY`。

Migration 必须遵守共享平台全局锁；不得与 Procurement、Marketing 或 Shared Platform migration 并行创建。

---

# PF01 Portal Registry、Manifest 与 Route/Grant 契约

状态：`READY`

## 目标

先建立 Logical Portal 的正式契约和静态 Registry，不创建业务 migration。

## 允许修改范围

- `backend/app/core/portal_registry.py`，新增
- `backend/app/schemas/portal_manifest.py`，新增
- `backend/app/api/v1/endpoints/portal_manifest.py`，新增
- `frontend-h5/composables/usePortalManifest.ts`，新增
- `frontend-admin/composables/usePortalManifest.ts`，新增
- `frontend-pc/composables/usePortalManifest.ts`，新增
- Portal registry / manifest 测试
- 本文档 PF01 状态和交付记录

## 必须实现

- Registry 包含 PC、H5、Admin 全部 Logical Portal。
- H5 至少包含 customer、partner_company、field_worker、supplier、kiosk。
- Admin 至少包含第 2.4 节工作台。
- Manifest 包含 layout、home、menu、route allowlist、required grants、theme 和 PWA key。
- 未知 Portal fail closed。
- Manifest 不授予权限，只描述体验。
- 当前旧 Portal Mode 继续兼容，但必须标记迁移目标。

## 禁止范围

- 不创建 migration。
- 不实现 Membership。
- 不增加新的前端工程。
- 不停止或合并当前 Portal 容器。
- 不修改外部系统。

## 验证重点

- 五种 H5 Manifest 明显不同。
- Partner Company 看不到 Field Worker 专用流程。
- Field Worker Manifest 不包含 RFQ 报价、利润、公司设置。
- Supplier Manifest 不包含现场施工任务。
- Admin 工作台有独立菜单与 Grant 要求。
- 未知 Portal 和伪造 Portal 被拒绝。

## 交付记录

```text
实现 Agent：
实现日期：
主要文件：
自测结果：
已知限制：

验证 Agent：
验证日期：
验证结果：
结论：VERIFIED / 退回 IN_PROGRESS
```

---

## 9. 后续栏目验收定义

### PF02 Workspace、Membership 与 Portal Grant

- 新增正式模型和 migration。
- 一个账号多 Membership。
- Portal 切换与 Grant 审计。
- 幂等迁移现有 `User.role`。

### PF03 Field Service Domain

- 新增 Crew、Worker、WorkPackage、FieldTask、Assignment、Evidence。
- Worker 不需要 `ServicePartner` 主档案。
- MaintenanceSchedule 只生成维保 FieldTask。

### PF04 Field Operations Admin

- WorkPackage、Crew、Worker、技能、证书、调度、地图、异常、验收队列。
- Project Manager 只看到授权 Region / Workspace。

### PF05 Partner Company H5

- RFQ、Bid、WorkPackage、Crew、Worker、排期和绩效。
- 不展示 Worker 个人任务执行界面。

### PF06 Field Worker PWA

- 完成第 6 节所有能力和离线冲突测试。
- 不展示报价、利润或公司管理。

### PF07 Supplier H5

- 供应商 RFQ、报价、目录、订单、发货、质保。
- 与 Partner Company、Field Worker 权限隔离。

### PF08 Customer H5

- 需求、项目、计划、审批、验收、资产、保修、AMC、Ticket。
- 客户只看到自己的对象。

### PF09 三物理前端收敛

- 逻辑 Portal 不再要求复制代码工程。
- 动态 Theme/Menu/Manifest/PWA metadata。
- 当前兼容端口迁移方案必须可回滚。

### PF10 发布闸门

固定角色 E2E：

```text
Customer Owner
Partner Company Owner
Partner Dispatcher
Crew Lead
Electrician Worker
Installer Worker
Maintenance Worker
Supplier Operator
Project Manager
Marketing Operator
AI Supervisor
Finance / Audit
Kiosk Device
```

必须验证跨 Portal、跨 Workspace、跨 Region、撤权、离线缓存和对象级越权。

还必须验证：

- 测试身份可幂等 seed 和清除。
- Production 环境无法使用测试身份或固定演示密码。

---

## 10. Agent 提示词

### 实现 Agent

```text
读取：
/Users/mac/Code_Start/Aislos/Ainerwise/docs/PORTAL_FIELD_SERVICE_V1_TASKS.md
/Users/mac/Code_Start/Aislos/SHARED_PLATFORM_MIDDLEWARE_PLAN.md
/Users/mac/Code_Start/Aislos/Ainerwise/AGENTS.md

只领取 Portal & Field Service 文档中唯一 READY 栏目。
开始前将栏目改为 IN_PROGRESS。
严格遵守允许修改范围。
不得新增第四套前端代码基座。
不得让 Worker 依赖 ServicePartner 主档案。
如需 migration，必须先获得全局 migration 锁。
完成后填写交付记录并改为 READY_FOR_VERIFY。
不得自行标记 VERIFIED。
```

### 验证 Agent

```text
读取：
/Users/mac/Code_Start/Aislos/Ainerwise/docs/PORTAL_FIELD_SERVICE_V1_TASKS.md

只验证当前 READY_FOR_VERIFY 栏目。
检查不同 Logical Portal 的布局、菜单、路由、API 和对象级权限。
检查 Worker 只能访问有效 Assignment。
检查跨 Portal、跨 Workspace、跨 Region 和撤权失败路径。
验证通过后标记 VERIFIED，并只解锁下一栏目。
不要实现下一栏目。
```

---

## 11. 当前下一步

当前唯一可领取 Portal & Field Service 任务：

> `PF01 Portal Registry、Manifest 与 Route/Grant 契约`

PF01 不创建 migration，可以与其他非重叠任务并行。
