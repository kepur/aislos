# AinerWise 给 Codex / Claude 的补充实现说明

> 本文档是在《AinerWise B2B 智能建筑/能源系统集成平台规划》基础上的补充。目标不是重新写商业计划，而是把 Wei 的职业路线、个人优势、当前阶段限制、AI 编码实现策略、MVP 优先级和 Codex/Claude 可执行任务拆清楚。

---

## 0. 背景定位：为什么这个系统要这样做

AinerWise 不是传统电商，也不是纯 SaaS。它是一个围绕“欧洲本地智能建筑/能源系统集成”的 B2B 业务操作系统。

创始人 Wei 的现实情况：

- 有网络与系统工程背景，熟悉 Linux、Docker、Kubernetes、网关、API、自动化、AI 工具链；
- 正在考虑在塞尔维亚/波兰等欧洲区域落地，前期可能从 KNX、弱电、智能化、CCTV、Home Assistant、光伏监控、基础维护服务切入；
- 目前还不是成熟 KNX/楼宇自动化大工程商，所以第一阶段不能假装自己已经有大量项目履历；
- 未来希望做“技术型关系节点”：连接本地客户、本地施工/服务伙伴、中国供应商、AI 方案能力和长期运维服务；
- 业务核心不是卖便宜货，而是“方案 + 设备 + 安装调试 + 质保 + 长期维护”。

因此系统必须支持两个阶段：

1. **早期可信落地阶段**：官网、解决方案展示、需求收集、产品库、供应商申请、后台 Lead 管理、Telegram 通知、AI 初步方案。
2. **后期项目运营阶段**：供应商门户、报价、项目管理、采购、工单、质保、备用件、服务包、多区域、多语言。

---

## 1. 最重要的产品原则

### 1.1 不是商城，先做 Lead-to-Solution

前台可以展示产品，但默认动作不要是“直接购买”。

推荐动作优先级：

1. Submit Requirement
2. Request Quote
3. Add to Project
4. Ask for Solution
5. Book Site Assessment

复杂设备和 KNX/智能建筑系统不能像普通商品一样直接下单，因为必须确认现场条件、兼容性、安装、售后、质保和服务区域。

### 1.2 网站要建立可信感，而不是炫技感

前台风格：

- 高端 B2B；
- 欧洲本地化；
- 科技但不浮夸；
- 不要像低价批发站；
- 强调 local service、verified suppliers、lifecycle support、AI-assisted planning。

### 1.3 后台比前台更重要

AinerWise 的核心资产不是首页，而是后台逐步沉淀：

- 客户需求；
- 供应商能力；
- 产品参数；
- 区域服务能力；
- 项目报价经验；
- 工单与质保记录；
- AI 方案知识库。

### 1.4 AI 只能生成草案，不能自动承诺

所有 AI 输出必须标注：

> Preliminary recommendation. Final solution requires engineering review and site verification.

后台必须有人审查后才能发给客户。

---

## 2. 根据 Wei 职业规划需要补充的模块

原文档已经包含基础平台功能，但结合 Wei 的职业路线，需要重点补充以下模块。

---

## 3. 个人服务能力档案模块：Founder Capability Profile

早期 Wei 还没有大量公司案例，但可以展示“个人能力 + 可提供服务”。

### 3.1 用途

前台可以有一个低调但可信的 Founder / Technical Lead 区域，强调：

- IT/network/system engineering background；
- smart building automation learning path；
- AI-assisted solution planning；
- China supply chain coordination；
- local partner collaboration。

不要吹成大型工程公司，而是表达为：

> AinerWise starts as a focused smart building integration studio, combining IT automation, supplier sourcing, and local service partners.

### 3.2 后台字段

新增表：`founder_profile` 或 CMS 配置。

字段：

- id
- name
- title
- bio_short
- bio_long
- skills_json
- certifications_json
- service_regions_json
- languages_json
- visible_on_site
- updated_at

### 3.3 前台展示原则

不要过度个人化。展示为 Technical Lead / Founder 即可。

---

## 4. 学习与认证进度模块：Certification Roadmap

Wei 计划考 KNX Basic，并可能继续 Advanced、HVAC、Energy。这个进度可以作为内部运营和前台可信度来源。

### 4.1 后台用途

后台记录自己和未来团队/服务伙伴的证书：

- KNX Basic
- KNX Advanced
- KNX HVAC Specialist
- KNX Energy Management
- Electrician / low-voltage local qualification
- Solar / PV related certificates
- Vendor training certificates

### 4.2 数据模型

`certification_records`

- id
- owner_type: founder / employee / service_partner / vendor
- owner_id
- certification_name
- issuer
- country
- status: planned / studying / passed / expired
- issue_date
- expiry_date
- certificate_file_url
- public_visible
- notes

### 4.3 前台逻辑

只有 passed 且 public_visible=true 的证书显示在前台。

正在学习的证书可以显示成 Roadmap，但不要伪装成已获得。

---

## 5. 服务伙伴网络模块：Local Partner Network

这是非常关键的补充。Wei 的路线不是自己一人施工，而是组织资源。

### 5.1 伙伴类型

- Electrician
- KNX Programmer
- HVAC Technician
- CCTV Installer
- Network Engineer
- Solar/PV Technician
- General Contractor
- Interior/Renovation Partner
- Translation/Local Coordinator

### 5.2 数据模型

`service_partners`

- id
- company_id
- partner_type
- country
- city
- service_radius_km
- languages_json
- skills_json
- certifications_json
- hourly_rate
- day_rate
- project_rate_rule_json
- availability_status
- rating_internal
- public_visible
- verification_status
- telegram_chat_id
- notes_internal

### 5.3 项目匹配逻辑

Lead 创建后，后台根据：

- country/city
- required systems
- project size
- service urgency
- language
- certificate requirement

推荐服务伙伴。

MVP 可以先人工分配，后期再自动匹配。

---

## 6. 现场信息采集模块：Site Survey Intake

这比普通需求表单更重要，因为智能建筑方案高度依赖现场情况。

### 6.1 前台客户表单分层

不要一次性把客户吓跑。建议分 3 层：

#### Quick Lead Form

- country/city
- project type
- target system
- budget range
- contact
- short description

#### Detailed Site Survey

- building type
- area
- floors
- rooms
- existing wiring
- internet/router location
- electrical panel location
- HVAC type
- lighting type
- existing CCTV/access control
- solar/inverter/battery info
- preferred language
- files/photos/videos

#### Professional Survey Checklist

后台给你或服务伙伴使用：

- wiring route
- panel capacity
- network topology
- device mounting points
- KNX bus possibility
- Wi-Fi/Zigbee/Thread/LoRa constraints
- HVAC protocol availability
- Modbus/BACnet availability
- safety notes
- hidden costs

### 6.2 数据模型

`site_surveys`

- id
- lead_id
- survey_type: quick / detailed / professional
- survey_json
- uploaded_files_json
- completeness_score
- risk_score
- created_by
- created_at

### 6.3 AI 功能

AI 根据 site survey 输出：

- missing information
- site risks
- possible solution types
- estimated complexity
- recommended next action

---

## 7. 解决方案包模块：Solution Packages

Wei 早期缺少经验，所以最好把服务标准化成包，而不是每次从零解释。

### 7.1 推荐第一批方案包

1. **Smart Starter Retrofit**
   - 适合小公寓/商铺；
   - Home Assistant + sensors + smart switches + remote access；
   - 目标是低成本入门。

2. **CCTV & Access Control Upgrade**
   - 摄像头、NVR、门禁、远程访问、网络优化；
   - 最容易前期接单。

3. **Smart Hotel Room Control Lite**
   - 房卡/入住状态/灯光/空调基础联动；
   - 可先用轻量方案，后期再 KNX 化。

4. **KNX Lighting & Scene Control**
   - 灯光、场景、面板、传感器；
   - 适合有预算的新装修项目。

5. **Solar & Energy Monitoring Dashboard**
   - 逆变器/电表/能耗采集；
   - dashboard + alert + monthly report。

6. **Remote Maintenance Plan**
   - 对已安装系统做远程监控、升级、备份、故障响应。

### 7.2 数据模型

`solution_packages`

- id
- slug
- title
- target_customer_type
- suitable_regions_json
- included_systems_json
- recommended_products_json
- required_service_partner_types_json
- base_price_rule_json
- estimated_timeline_days
- risk_notes
- public_visible
- language_content_json

---

## 8. 产品兼容性矩阵：Compatibility Matrix

这是未来护城河。不要只存商品，要存“能不能一起工作”。

### 8.1 兼容维度

- KNX
- KNX/IP
- Modbus RTU/TCP
- BACnet
- MQTT
- Zigbee
- Z-Wave
- Matter/Thread
- Home Assistant
- Tuya
- DALI
- ONVIF
- RTSP
- PoE
- inverter protocol
- dry contact
- RS485

### 8.2 数据模型

`product_compatibility`

- id
- product_id
- protocol
- compatibility_level: native / gateway_required / partial / not_supported / unknown
- tested_by: official / vendor / partner / unknown
- test_status: untested / tested_ok / tested_with_notes / failed
- notes
- test_artifact_url
- updated_at

### 8.3 AI 使用

AI 推荐 BOM 时必须参考兼容性矩阵，避免瞎推荐。

---

## 9. 供应商分级与风险控制

平台前期如果开放供应商，风险很大。必须做分级。

### 9.1 供应商等级

- Pending
- Listed Only
- Verified
- Tested by AinerWise
- Strategic Partner
- Suspended

### 9.2 供应商风险字段

- documentation_quality_score
- english_support_score
- warranty_reliability_score
- spare_parts_support_score
- export_experience_score
- response_speed_score
- defect_history_json
- dispute_history_json

### 9.3 前台展示

前台只展示简单标签：

- Verified Supplier
- Service-ready
- Tested by AinerWise
- Local spare parts available

不要把内部评分暴露给客户。

---

## 10. 备用件/长期服务合同必须产品化

Wei 提到“卖 10 台准备 12/13 台”。这个思路正确，但要制度化。

### 10.1 服务年限建议

默认不要承诺永久服务。

建议前台提供：

- Basic Warranty Support: 1 year
- Standard Lifecycle Support: 3 years
- Extended Lifecycle Support: 5 years
- Commercial Lifecycle Support: 8 years
- Premium Enterprise Support: 10 years
- Custom Long-term Contract

### 10.2 服务合同要区分

- manufacturer warranty
- platform support
- local installation warranty
- spare parts reserve
- remote maintenance
- on-site response
- software/firmware update
- annual inspection

### 10.3 数据模型

`warranty_policies`

- id
- product_id
- supplier_id
- region
- manufacturer_warranty_months
- platform_support_months
- local_installation_warranty_months
- spare_parts_policy_json
- response_sla_json
- exclusions_text
- active

---

## 11. 报价系统要从一开始按“项目报价”设计

即使 MVP 不做完整报价，也要预留模型。

### 11.1 报价格式

报价不要只是商品价格。应该分：

- Equipment
- Integration Design
- Installation
- Commissioning
- Travel / Site Visit
- Support Package
- Spare Parts Reserve
- Logistics
- Tax / Duties
- Platform Fee
- Discount

### 11.2 报价状态

- Draft
- Internal Review
- Sent to Client
- Client Questions
- Revised
- Accepted
- Rejected
- Expired

### 11.3 PDF 输出

后期必须支持报价 PDF，多语言模板。

MVP 可以先后台生成结构化 quote，再手动导出。

---

## 12. Telegram 集成补充：不要一开始自动建太多群

Telegram 很适合，但早期自动建群会乱。

### 12.1 推荐分阶段

#### MVP

只做：

- Admin group notification
- New lead notification
- New supplier application notification
- New product pending review notification
- AI analysis completed notification

#### V2

增加：

- vendor private notification
- service partner notification
- project group creation manually approved by admin

#### V3

增加：

- auto project group creation
- bot command update status
- ticket sync
- quote approval reminders

### 12.2 Bot 命令建议

- `/lead <id>` 查看 Lead 摘要
- `/assign <lead_id> <user>` 分配负责人
- `/stage <project_id> <stage>` 更新项目状态
- `/ticket <project_id>` 创建工单
- `/quote <lead_id>` 查看报价摘要

---

## 13. LangGraph AI Orchestrator 设计补充

### 13.1 不要把 AI 直接塞进主后端

建议独立服务：`ai-orchestrator`。

主后端 FastAPI 负责业务数据。AI 服务负责分析、生成和匹配。

### 13.2 推荐 LangGraph 节点

1. `InputNormalizer`
   - 统一语言、单位、国家、项目类型。

2. `RequirementCompletenessChecker`
   - 判断缺哪些现场信息。

3. `ProjectClassifier`
   - 分类：CCTV / KNX / HVAC / Solar / Hotel / Villa / Retrofit / Maintenance。

4. `RiskAnalyzer`
   - 判断现场风险、预算风险、兼容风险、交付风险。

5. `SolutionPackageMatcher`
   - 匹配 solution_packages。

6. `ProductCategoryRecommender`
   - 只推荐品类，不直接承诺具体 SKU。

7. `CompatibilityChecker`
   - 查询兼容性矩阵。

8. `VendorMatcher`
   - 匹配供应商和服务伙伴。

9. `DraftSolutionGenerator`
   - 生成客户可读草案。

10. `AdminReviewSummaryGenerator`
    - 生成给管理员看的风险摘要。

11. `TelegramMessageGenerator`
    - 生成通知内容。

### 13.3 AI 输出必须存档

新增表：`ai_runs`

- id
- entity_type: lead / project / quote / ticket
- entity_id
- workflow_name
- input_json
- output_json
- model_name
- status
- error_message
- created_at

---

## 14. 前端体验补充

### 14.1 首页最重要的 CTA

第一屏只保留两个主按钮：

- Get a Smart Building Assessment
- Become a Supplier / Partner

不要在第一屏放太多商城入口。

### 14.2 解决方案页要有“预算等级”

每个方案页展示：

- Budget
- Standard
- Premium
- Enterprise

但不要写死价格，可以写 starting from 或 Request Quote。

### 14.3 产品页要强调“Service-ready”

产品卡片重点：

- works with which solution
- local service available or not
- spare parts policy
- verified/tested status
- request quote

---

## 15. 推荐技术栈落实版

考虑 Wei 的习惯和未来 AI 编码协作，推荐：

### 15.1 Monorepo

```text
ainerwise/
  apps/
    web/                 # Next.js/Nuxt frontsite + buyer portal
    admin/               # admin dashboard
    vendor/              # optional later vendor portal
  services/
    api/                 # FastAPI backend
    ai-orchestrator/     # LangGraph workflows
    worker/              # Celery/Dramatiq workers
    telegram-bot/        # Telegram bot worker
  packages/
    shared-types/
    ui/
    i18n/
  infra/
    docker-compose.yml
    nginx/
    postgres/
    minio/
  docs/
```

### 15.2 更适合 MVP 的简化版

为了减少复杂度，MVP 可以先：

```text
ainerwise/
  frontend/              # Nuxt 3 or Next.js
  backend/               # FastAPI
  ai_orchestrator/       # LangGraph, can call backend API
  telegram_bot/          # bot worker
  docs/
  docker-compose.yml
```

### 15.3 数据库

PostgreSQL 必须。

建议预留：

- pgvector：未来做产品/方案/供应商语义匹配；
- JSONB：存储规格、现场信息、AI 输出；
- full-text search：产品和方案搜索。

### 15.4 对象存储

MinIO：

- 产品图片；
- 现场照片；
- 图纸；
- 报价 PDF；
- 证书；
- 施工照片。

---

## 16. 安全与权限补充

B2B 平台必须防止供应商绕过平台抢客户。

### 16.1 联系方式保护

MVP 默认：

- Vendor 看不到 Buyer 的完整邮箱/电话；
- 供应商只收到平台整理后的需求摘要；
- 管理员决定是否开放联系。

### 16.2 权限隔离

- Buyer 只能看自己的 leads/projects/quotes/tickets；
- Vendor 只能看自己的 products/inquiries；
- Service Partner 只能看分配给他的 tasks；
- Admin 可以全局管理。

### 16.3 审计日志

新增表：`audit_logs`

- id
- actor_user_id
- action
- entity_type
- entity_id
- before_json
- after_json
- ip
- created_at

---

## 17. SEO 与内容策略补充

Wei 早期缺少案例，可以靠内容建立专业感。

### 17.1 初始内容栏目

- Smart Building Basics
- KNX vs Home Assistant
- Smart Hotel Energy Saving
- CCTV & Access Control Guide
- Solar Monitoring for Small Business
- Serbia Smart Building Guide
- China Supplier Selection Guide

### 17.2 不要伪造案例

没有真实项目时，用：

- Reference Architecture
- Example Solution
- Concept Package
- Demo Project

等说法。

---

## 18. MVP 重新排序

结合 Wei 当前职业阶段，MVP 优先级应该调整为：

### P0 必须

1. Landing page / 官网首页；
2. Solution pages；
3. Submit requirement；
4. Admin login；
5. Lead management；
6. Product catalog with official products；
7. Supplier application；
8. Telegram admin notifications；
9. AI lead analysis draft；
10. Multi-language foundation: English + Chinese，Serbian 可预留。

### P1 第二批

1. Vendor portal；
2. Product review workflow；
3. Service packages；
4. Quote draft；
5. Site survey checklist；
6. Service partner module；
7. MinIO file upload；
8. AI missing-info question generator。

### P2 第三批

1. Project management；
2. Tickets；
3. Warranty policy；
4. Spare parts policy；
5. Quote PDF；
6. Vendor notifications；
7. Project Telegram groups。

### P3 后续

1. Payment；
2. Contract；
3. Auto matching；
4. Mobile app/PWA；
5. Multi-region pricing；
6. Advanced AI BOM recommendation。

---

## 19. 给 Codex / Claude 的实现约束

### 19.1 不要一次性做完所有功能

AI 编码工具必须按阶段交付。每个阶段都要能运行、能测试、能演示。

### 19.2 优先做可工作的垂直闭环

第一条闭环：

```text
客户提交需求
→ 后台生成 Lead
→ AI 初步分析
→ Telegram 通知管理员
→ 管理员查看 Lead
```

第二条闭环：

```text
供应商提交申请
→ 后台审核
→ 供应商可登录
→ 上传产品
→ 管理员审核产品
→ 前台展示产品
```

第三条闭环：

```text
管理员创建服务包/解决方案
→ 前台展示
→ 客户从方案页提交需求
→ Lead 自动关联方案
```

### 19.3 所有复杂功能先用 admin-controlled

不要一开始让供应商和客户自由交易。

前期所有关键动作：

- 产品上架；
- 报价发送；
- 供应商联系客户；
- 项目建群；
- 服务承诺；

都必须管理员审核。

### 19.4 代码必须包含

- `.env.example`
- README
- docker-compose dev environment
- database migrations
- seed data
- basic tests
- role-based access control
- structured logging

---

## 20. 推荐 API 模块

后端 FastAPI 推荐 routers：

```text
/api/auth
/api/users
/api/companies
/api/solutions
/api/products
/api/leads
/api/site-surveys
/api/vendors
/api/service-partners
/api/service-packages
/api/quotes
/api/projects
/api/tickets
/api/files
/api/ai-runs
/api/integration-events
/api/admin
```

---

## 21. 数据库表补充清单

在原文档基础上建议增加：

- founder_profile
- certification_records
- service_partners
- site_surveys
- solution_packages
- product_compatibility
- warranty_policies
- ai_runs
- audit_logs
- file_assets
- regions
- currencies
- translation_entries
- vendor_risk_profiles
- partner_assignments

---

## 22. Codex / Claude 任务拆分建议

### Task A：项目骨架

目标：创建 monorepo 或简化版项目结构。

交付：

- frontend
- backend
- docker-compose
- postgres
- redis
- minio
- README
- env example

### Task B：数据库与基础 API

交付：

- SQLAlchemy models / Alembic migrations
- auth
- roles
- companies
- products
- leads
- suppliers
- solutions

### Task C：前台 MVP

交付页面：

- home
- solutions list/detail
- products list/detail
- submit requirement
- supplier application
- contact

### Task D：后台 MVP

交付页面：

- dashboard
- leads
- products
- supplier applications
- solutions
- AI runs
- integration events

### Task E：Telegram Bot

交付：

- bot token config
- admin group chat id config
- event worker
- lead.created notification
- vendor.applied notification
- product.submitted notification
- ai.completed notification

### Task F：AI Orchestrator

交付：

- LangGraph workflow
- lead analysis endpoint
- missing info checker
- solution package matcher
- admin summary generator
- ai_runs persistence

### Task G：文件上传

交付：

- MinIO integration
- product images
- lead files/photos
- certification files
- quote attachments

### Task H：i18n

交付：

- English / Chinese initial translations
- language switcher
- translatable solution/product fields prepared

---

## 23. 第一版 Seed Data

为了方便演示，系统应内置演示数据。

### 23.1 Solutions

- Smart Hotel Lite
- Smart Villa Retrofit
- CCTV & Access Control Upgrade
- KNX Lighting Automation
- Solar & Energy Monitoring
- Remote Maintenance Plan

### 23.2 Product Categories

- KNX Devices
- Gateways
- Sensors
- Smart Panels
- CCTV
- Access Control
- Network Devices
- Energy Meters
- Solar Monitoring
- Service Packages

### 23.3 Service Packages

- Basic Support 1 Year
- Standard Support 3 Years
- Lifecycle Support 5 Years
- Commercial Support 8 Years
- Premium Support 10 Years

### 23.4 Regions

- Serbia
- Poland
- New Zealand
- Australia

MVP active region：Serbia。

---

## 24. 需要 AI 设计 UI 时的风格提示

给 Stitch / Claude / Codex 前端设计时使用：

```text
Design a premium B2B smart building and energy integration platform named AinerWise. The visual style should feel European, professional, technical, trustworthy, and modern. Avoid cheap marketplace aesthetics. The platform sells solution-ready devices, local integration services, lifecycle support, and AI-assisted smart building planning. Primary users are hotels, villas, apartments, shops, commercial buildings, suppliers, and service partners. Use clean layouts, strong hero sections, solution cards, trust badges, service package blocks, and clear CTAs such as Submit Project Requirement and Become a Supplier.
```

---

## 25. 最终执行建议

Wei 不应该先做一个“大而全平台”。

最正确的第一版是：

> 高端 B2B 官网 + 需求收集 + 产品目录 + 供应商申请 + 后台 Lead 管理 + Telegram 通知 + AI 初步分析。

这个版本既能服务真实业务，也能给未来扩展留下空间。

真正赚钱的长期方向不是产品交易抽佣，而是：

1. 项目方案设计费；
2. 集成与调试费；
3. 本地安装服务；
4. 长期维护服务包；
5. 设备加价与供应商佣金；
6. 备用件与质保合同；
7. 区域服务伙伴网络；
8. AI Energy / Smart Building 运维。

AinerWise 的核心不是“卖设备”，而是成为：

> 面向欧洲本地客户的 AI-assisted Smart Building & Energy Integration Operator。

