# AinerWise 前后台功能细化与长期维护 / 项目记账 / 质保责任设计

> 版本：v0.5  
> 用途：直接交给 Codex / Claude / Cursor / Windsurf，对当前 AinerWise 系统继续细化改造。  
> 核心目标：把 AinerWise 从“方案展示 + 初步报价平台”升级为“项目线索、方案、报价、项目记账、供应商质保、备件库存、年度维护费、长期 LTV 管理”的完整业务系统。  
> 重要原则：AinerWise 不应该把所有硬件质量风险都无脑背到自己身上，而应该通过“标准服务边界 + 供应商质保记录 + 备件池 + AMC 年度维护合同 + 客户付费升级服务”来控制风险和形成长期饭票。

---

# 1. 最终商业模式定义

AinerWise 的收入分成 6 类，不要只看设备利润。

## 1.1 一次性收入

1. Phase-1 方案设计费  
2. 现场勘查费  
3. 系统架构设计费  
4. 设备销售差价  
5. 安装 / 调试 / 集成费  
6. 项目管理费  
7. 平台服务费  
8. 培训和交付文档费  

## 1.2 长期收入

1. AMC 年度维护合同  
2. 远程监控平台费  
3. 报警值守费  
4. 合规报表费  
5. 校准费  
6. 备件 / 探头 / 标签 / 电池更换费  
7. 系统升级费  
8. 节能优化顾问费  
9. 多站点管理费  
10. 续约服务费  

## 1.3 推荐商业结构

前期项目报价不要只写：

```text
设备费 + 安装费
```

而要拆成：

```text
设备费
+ 方案设计费
+ 安装实施费
+ 系统集成费
+ 项目管理费
+ 平台服务费
+ 首年基础支持
+ 可选 AMC 年度维护合同
+ 可选备件包
```

这样客户从第一天就知道：AinerWise 是长期服务商，不是卖完设备就消失的贸易商。

---

# 2. 你是否应该直接服务客户？

## 2.1 结论

最优模式不是完全甩锅给供应商，也不是所有责任都自己背。

最佳模式是：

> AinerWise 对客户提供“系统级服务责任”，供应商对 AinerWise 提供“设备级质保责任”。

也就是说：

- 客户找 AinerWise；
- AinerWise 判断是系统配置问题、安装问题、网络问题、设备硬件问题、客户误操作，还是供应商质量问题；
- 如果是设备质量问题，AinerWise 对接供应商；
- 如果是服务合同覆盖范围内，AinerWise 处理；
- 如果超出服务合同，客户按工单付费。

这比让客户直接找中国供应商靠谱，也比你无边界背锅安全。

---

## 2.2 不建议完全甩给供应商

不要对客户说：

> 设备坏了你自己找供应商。

这会让你变成低级中间商，客户不会愿意签长期维护合同。

你应该说：

> AinerWise 负责系统级支持和故障协调，设备本体按供应商质保政策执行；高级维护包可包含快速换新、备件池和现场服务。

这样你既有服务价值，又能控制责任边界。

---

## 2.3 不建议你无条件包所有硬件

也不要说：

> 所有设备坏了我都免费换。

这会把你拖死，尤其是中国供应链设备、跨境物流、客户使用环境复杂时。

正确方式是分层：

| 层级 | 客户权益 | 你的责任 |
|---|---|---|
| Standard Warranty Pass-through | 按供应商质保执行 | 协助判断、提交质保、协调处理 |
| AinerWise Managed Warranty | 你提供统一窗口 | 你先处理客户，再找供应商追偿 |
| Fast Replacement Plan | 快速换新 | 客户付费购买，你用备件池快速替换 |
| Premium AMC | 长期维护 | 包含巡检、远程支持、优先响应、部分备件 |
| Excluded Damage | 人为损坏、进水、雷击、错误使用 | 另行报价 |

---

# 3. 设备质保与备件策略

## 3.1 供应商质保字段

后台 Supplier / Product 必须记录：

```yaml
SupplierWarranty:
  supplier_id:
  product_id:
  warranty_years:
  warranty_type: repair | replacement | parts_only | return_to_factory
  shipping_responsibility: supplier | ainerwise | customer | shared
  response_time_days:
  replacement_policy:
  spare_parts_available: true/false
  firmware_support: true/false
  remote_debug_support: true/false
  api_protocol_support: true/false
  warranty_region_limit:
  notes:
```

---

## 3.2 客户侧质保字段

客户项目里必须记录：

```yaml
CustomerWarranty:
  project_id:
  customer_id:
  warranty_model: pass_through | managed | fast_replacement | premium_amc
  start_date:
  end_date:
  included_devices:
  excluded_devices:
  included_labor: true/false
  included_remote_support: true/false
  included_on_site_visits_per_year:
  spare_parts_included: true/false
  max_claims_per_year:
  notes:
```

---

## 3.3 备件池策略

你应该对不同产品设置备件比例。

建议：

| 产品类型 | 建议备件比例 |
|---|---:|
| 关键网关 / 控制器 | 5% - 10% |
| 温湿度传感器 | 10% - 15% |
| 水质探头 | 15% - 25% |
| 厨房安全探头 | 10% - 20% |
| BLE / LoRa 标签 | 10% - 20% |
| 普通面板 / 开关 | 3% - 8% |
| 摄像头 | 5% - 10% |
| 电池 / 校准液 / 小耗材 | 20%+ |

备件成本不要自己硬扛，应该进入报价结构：

```text
Spare Parts Reserve / 备件预留费
```

或者打包进 AMC。

---

## 3.4 备件收费方式

三种模式：

### 模式 A：客户购买备件包

适合中大型项目。

报价里显示：

```text
Recommended Spare Parts Kit: 5% - 12% of hardware cost
```

备件归客户所有，但由 AinerWise 管理。

优点：你风险低。  
缺点：报价变高。

---

### 模式 B：AinerWise 自建备件池

适合你有多个同类项目后。

你统一买常用备件，用于多个客户快速替换。

优点：体验好，利润高。  
缺点：占库存和现金流。

---

### 模式 C：高级 AMC 包含快速换新

客户每年多付费，你提供快速替换服务。

优点：长期饭票最强。  
缺点：必须严格限制范围和次数。

---

# 4. AMC 年度维护合同设计

## 4.1 AMC 是你的长期饭票核心

所有项目都应该尽量绑定 AMC。

AMC 不是可有可无的售后，而是业务核心：

```text
Annual Maintenance Contract = 年度维护合同 = 长期现金流
```

---

## 4.2 AMC 计费方式

支持多种计费公式：

### 公式 A：按项目总造价百分比

适合 BuildingBrain / EnergyGuard / FactoryPulse。

```text
Annual AMC Fee = Project Total Value × 5% - 12%
```

建议范围：

| 项目类型 | AMC 百分比 |
|---|---:|
| BuildingBrain | 5% - 10% |
| EnergyGuard | 5% - 12% |
| StorageGuard | 8% - 18% |
| AquaGuard | 12% - 25% |
| KitchenGuard | 8% - 18% |
| FactoryPulse | 8% - 15% |
| AssetPulse | 10% - 20% |

AquaGuard 高是因为探头、校准、耗材多。

---

### 公式 B：按点位收费

适合 StorageGuard / AquaGuard / KitchenGuard / AssetPulse。

```text
Annual AMC Fee = Base Fee + Monitoring Point Fee × Quantity
```

示例：

```text
Base Fee: €300/year
Temperature Point: €30-80/year
Water Quality Probe: €150-500/year
Kitchen Safety Node: €50-150/year
Asset Tag: €5-30/year
Gateway: €50-200/year
```

---

### 公式 C：按站点收费

适合多店铺、多仓库、多厨房客户。

```text
Annual AMC Fee = Site Fee × Number of Sites + Point Fee
```

---

### 公式 D：按服务等级收费

适合富人别墅 / 酒店 / 企业客户。

| 套餐 | 年费逻辑 |
|---|---|
| Basic | 低价，远程支持为主 |
| Compliance | 报表 + 校准 + 年检 |
| Commercial | 远程 + 现场 + 备件 |
| Premium | 专属支持 + 快速响应 + 系统优化 |

---

## 4.3 AMC 套餐建议

### Basic AMC

适合：小项目、小冷库、小餐厅、小别墅。

包含：

- 远程支持；
- 基础报警；
- 每年一次系统检查；
- 基础报表；
- 不含耗材；
- 不含现场紧急服务。

---

### Compliance AMC

适合：冷链、水质、厨房安全。

包含：

- 合规报表；
- 年度校准；
- 探头检查；
- 报警联系人维护；
- 电子维护记录；
- 基础耗材折扣；
- 可选现场服务。

---

### Commercial AMC

适合：酒店、公寓、工厂、仓库。

包含：

- 远程监控；
- 多点位管理；
- 年度现场巡检；
- 固件升级；
- 小范围逻辑调整；
- 备件优先供应；
- 季度报告。

---

### Premium AMC

适合：高端别墅、大客户、多站点客户。

包含：

- 优先响应；
- 专属支持；
- 现场巡检 2-4 次/年；
- 关键备件池；
- 系统优化；
- 能耗报告；
- AI 分析报告；
- 家庭 / 员工权限维护；
- 高级自动化策略调整。

---

# 5. 项目记账功能

后台必须有项目财务模块，不然你后面不知道哪类项目真的赚钱。

## 5.1 Project Finance 数据结构

```yaml
ProjectFinance:
  project_id:
  customer_id:
  solution_line:
  currency:
  quoted_total:
  contract_total:
  hardware_revenue:
  design_fee:
  installation_fee:
  integration_fee:
  platform_fee:
  project_management_fee:
  amc_fee_year_1:
  amc_fee_annual:
  consumable_revenue_estimate:
  calibration_revenue_estimate:
  report_revenue_estimate:
  alarm_monitoring_revenue_estimate:
  supplier_cost:
  shipping_cost:
  customs_cost:
  local_installer_cost:
  labor_cost:
  travel_cost:
  spare_parts_cost:
  warranty_reserve_cost:
  gross_profit:
  gross_margin_percent:
  first_year_profit:
  annual_recurring_profit:
  ltv_3_year:
  ltv_5_year:
  ltv_8_year:
```

---

## 5.2 成本项必须细分

不要只记一个成本。

必须拆：

- 硬件采购成本；
- 国际物流；
- 清关 / 税费；
- 本地安装团队成本；
- 你的人工时间；
- 外包工程师；
- 差旅；
- 备件；
- 质保准备金；
- 平台服务器；
- Telegram / SMS 成本；
- 校准工具；
- 现场检测设备；
- 售后工单成本。

---

## 5.3 项目利润计算

后台自动计算：

```text
Gross Profit = Contract Total - Direct Cost
Gross Margin = Gross Profit / Contract Total
First-Year Profit = First-Year Revenue - First-Year Cost
Annual Recurring Profit = Annual Recurring Revenue - Annual Service Cost
LTV 3 Year = First-Year Profit + 2 × Annual Recurring Profit
LTV 5 Year = First-Year Profit + 4 × Annual Recurring Profit
```

---

## 5.4 项目抽点 / 平台费

你可以设置平台费规则：

```yaml
PlatformFeeRule:
  solution_line:
  fee_type: percentage | fixed | hybrid
  percentage:
  fixed_fee:
  min_fee:
  max_fee:
```

建议：

| 类型 | 平台 / 项目管理费 |
|---|---:|
| 小型项目 | 固定 €200 - €1000 |
| 中型项目 | 5% - 10% |
| 大型项目 | 3% - 8% |
| Phase-1 Proposal | 固定收费 |
| 设计-only | 10% - 20% 设计服务毛利 |
| 供应商撮合 | 3% - 15% 佣金 |

---

# 6. 报价生成器功能

## 6.1 报价必须拆层

报价页面必须包含：

```text
Hardware Package
Design & Engineering
Installation & Commissioning
Platform Setup
Project Management
Spare Parts Reserve
First-Year Support
Annual Maintenance Contract
Optional Fast Replacement Plan
Optional Compliance Reporting
Optional Alarm Monitoring
```

---

## 6.2 客户看到的报价

客户不应该看到你的真实供应商成本。

客户看到的是：

- Monitoring Package；
- Control Package；
- Gateway Package；
- Compliance Package；
- AI Assessment Package；
- AMC Package；
- Spare Parts Kit。

---

## 6.3 内部报价视图

管理员看到：

- 真实品牌；
- 真实型号；
- 采购成本；
- 供应商；
- 交期；
- 质保；
- 毛利；
- 替代品；
- 风险；
- 备件建议。

---

# 7. 前台功能补充

## 7.1 Public Website 页面

必须包含：

1. 首页  
2. AI Facility Brain Demo  
3. Solutions Matrix  
4. BuildingBrain  
5. EnergyGuard  
6. StorageGuard  
7. KitchenGuard  
8. AquaGuard  
9. FactoryPulse  
10. AssetPulse  
11. VillaBrain  
12. Recurring Solutions  
13. AMC 年度维护合同  
14. Supplier Portal  
15. Demo Login  
16. Contact / Request Assessment  

---

## 7.2 每个解决方案页面功能

每个产品线页面要有：

- 场景图；
- 客户痛点；
- 典型风险；
- 系统组成；
- 监测点位；
- 报警方式；
- 报表样例；
- 服务包；
- 年度维护；
- 耗材 / 校准周期；
- 推荐合同年限；
- CTA。

---

## 7.3 前台不要暴露具体设备价格

客户看到的是：

```text
Temperature Monitoring Point
Kitchen Safety Node
Water Quality Probe Package
KNX Room Control Package
Energy Gateway Package
Machine Monitoring Point
```

而不是：

```text
某某品牌型号 29 欧
```

避免客户自己网上比价。

---

# 8. Buyer Portal 功能补充

## 8.1 Dashboard

显示：

- Active Projects；
- AI Assessment Progress；
- Proposal Status；
- Pending Documents；
- Monitoring Points；
- AMC Status；
- Upcoming Maintenance；
- Warranty Expiry；
- Open Tickets；
- Reports；
- Payment / Invoice Status。

---

## 8.2 Project Workspace

每个项目有：

1. Overview；
2. Site Data；
3. Files；
4. AI Assessment；
5. Proposal Plans；
6. BOM Sheet；
7. Finance Summary；
8. AMC Plan；
9. Warranty；
10. Tickets；
11. Reports；
12. Messages；
13. Timeline。

---

## 8.3 BOM Sheet

类似 Excel，支持：

- 数量修改；
- 已有设备标记；
- AinerWise 供货；
- 客户自备；
- 需要安装；
- 设计-only；
- 替换产品；
- 自动计算；
- 导出 PDF / Excel；
- 管理员锁价。

---

## 8.4 AMC 页面

客户可以看到：

- 当前维护套餐；
- 年费；
- 覆盖范围；
- 下一次巡检；
- 下一次校准；
- 备件状态；
- 已用服务次数；
- 不包含项目；
- 续约按钮。

---

## 8.5 Warranty 页面

客户可以看到：

- 每个设备的质保到期日；
- 供应商质保；
- AinerWise 服务覆盖；
- 是否支持快速换新；
- 是否需要付费；
- 工单入口。

---

## 8.6 Ticket / 工单

客户可以提交：

- 设备故障；
- 报警误报；
- 网络问题；
- 报表问题；
- 需要增加点位；
- 需要校准；
- 需要现场服务；
- 需要升级。

工单必须记录：

```yaml
Ticket:
  project_id:
  customer_id:
  type:
  priority:
  affected_device:
  warranty_related:
  amc_covered:
  estimated_cost:
  status:
  assigned_to:
  resolution:
```

---

# 9. Admin 后台功能补充

## 9.1 Admin Dashboard

显示：

- 今日新 Lead；
- 高意向 Lead；
- 高 LTV Lead；
- 本月报价金额；
- 本月成交金额；
- 本月 ARR；
- 即将到期 AMC；
- 即将到期质保；
- 待校准设备；
- 待更换耗材；
- 未处理工单；
- 项目毛利排行。

---

## 9.2 Lead 管理

字段：

- Lead Score；
- Recurring Revenue Score；
- Project Type；
- Budget；
- Region；
- Solution Line；
- Expected ARR；
- Expected LTV；
- Next Follow-up；
- Stage。

阶段：

```text
Cold
Warm
Qualified
Phase-1 Ready
Proposal Sent
Negotiation
Contract Pending
Won
Lost
AMC Active
Renewal Due
```

---

## 9.3 Project Admin

管理员可以管理：

- 项目资料；
- 客户信息；
- 方案；
- BOM；
- 供应商；
- 成本；
- 报价；
- 合同；
- 发票；
- 收款；
- AMC；
- Warranty；
- Tickets；
- Reports。

---

## 9.4 Supplier 管理

供应商字段：

```yaml
Supplier:
  name:
  country:
  categories:
  contact:
  payment_terms:
  warranty_policy:
  spare_parts_policy:
  moq:
  lead_time_days:
  remote_support:
  api_docs_available:
  certification:
  rating:
  notes:
```

供应商评价：

- 质量；
- 交期；
- 响应速度；
- 质保配合；
- 文档完整性；
- 价格稳定性；
- 是否适合长期合作。

---

## 9.5 Inventory / Spare Parts

必须有备件库存。

字段：

```yaml
InventoryItem:
  product_id:
  location:
  quantity:
  reserved_for_project:
  min_stock_level:
  reorder_level:
  supplier_id:
  cost:
  expiry_date:
  last_checked:
```

功能：

- 低库存提醒；
- 备件绑定项目；
- 备件出库记录；
- 备件成本计入项目；
- 过期耗材提醒。

---

# 10. 维护与校准管理

## 10.1 Maintenance Schedule

```yaml
MaintenanceSchedule:
  project_id:
  device_id:
  task_type: inspection | calibration | battery_replace | probe_replace | firmware_update | report_review
  due_date:
  frequency_months:
  assigned_to:
  status:
  cost:
  covered_by_amc: true/false
```

---

## 10.2 Calibration Record

```yaml
CalibrationRecord:
  device_id:
  project_id:
  calibration_date:
  next_due_date:
  calibration_method:
  certificate_file:
  technician:
  result:
  notes:
```

---

## 10.3 消耗品管理

适合：

- pH 探头；
- 校准液；
- 温湿度传感器电池；
- BLE 标签电池；
- 燃气探头；
- 水浸探头；
- 过滤器；
- 传感器保护套。

---

# 11. Telegram / WhatsApp 通知

## 11.1 管理员通知

事件：

- New High LTV Lead；
- Phase-1 Requested；
- Quote Approved；
- Contract Signed；
- Payment Due；
- AMC Renewal Due；
- Warranty Expiring；
- Calibration Due；
- Probe Replacement Due；
- Ticket Opened；
- High Priority Alarm；
- Supplier Warranty Claim Needed。

---

## 11.2 客户通知

事件：

- 报警；
- 报表生成；
- 校准到期；
- 维护预约；
- 工单更新；
- 续费提醒；
- 设备质保到期。

---

# 12. 法务和责任边界

## 12.1 合同里必须区分

1. 设备供应；
2. 安装实施；
3. 系统集成；
4. 平台服务；
5. 质保协调；
6. 现场服务；
7. 人为损坏；
8. 不可抗力；
9. 第三方网络 / 电力 / 云服务；
10. 客户自行改动导致的问题。

---

## 12.2 建议写法

客户合同中应写：

```text
AinerWise provides system integration, monitoring, support coordination and lifecycle service. Hardware warranty follows the original supplier warranty policy unless the customer purchases AinerWise Managed Warranty or Fast Replacement Plan.
```

中文：

```text
AinerWise 提供系统集成、监测、支持协调和长期运维服务。硬件本体质保默认遵循原供应商质保政策；如客户购买 AinerWise 托管质保或快速换新服务，则按对应服务包执行。
```

---

## 12.3 不保内容

明确排除：

- 人为损坏；
- 进水；
- 雷击；
- 客户私自拆改；
- 第三方施工破坏；
- 断电 / 网络运营商问题；
- 客户未续费；
- 客户拒绝维护导致的问题；
- 超过设备寿命周期。

---

# 13. 推荐报价结构模板

## 13.1 小型冷链项目

```text
StorageGuard Starter Package

Hardware & Gateway Setup: €X
Installation & Commissioning: €X
Platform Setup: €X
First-Year Support: Included
Annual Compliance AMC from Year 2: €X/year
Calibration: €X/year
Battery / Sensor Replacement: billed as needed or included in AMC
```

---

## 13.2 商用厨房项目

```text
KitchenGuard Safety Package

Gas / CO / Water Leak Monitoring Nodes: €X
Cutoff Valve Integration: €X
Alarm Setup: €X
Annual Safety Inspection: €X/year
Alarm Monitoring: €X/month
Premium AMC: Optional
```

---

## 13.3 别墅项目

```text
VillaBrain Privacy-First Smart Home Package

Design & System Architecture: €X
KNX / HA / Network / Security Package: €X
Installation & Commissioning: €X
Local AI / Energy Dashboard: Optional
Premium Villa Care AMC: €X/year
Fast Replacement Plan: Optional
```

---

# 14. 给 Codex / Claude 的直接执行 Prompt

```text
Upgrade AinerWise with detailed front-end and back-end features for project finance, AMC, warranty, supplier warranty, spare parts, long-term service revenue, and recurring LTV management.

AinerWise should not only generate AI proposals. It must manage the full lifecycle:
Lead -> AI Assessment -> Phase-1 Proposal -> Quote -> Contract -> Project Finance -> BOM -> Supplier Cost -> Installation -> Warranty -> AMC -> Maintenance -> Calibration -> Consumables -> Tickets -> Renewal.

Add Project Finance module:
hardware revenue, design fee, installation fee, integration fee, platform fee, project management fee, AMC fee, consumables, calibration, report fee, alarm monitoring, supplier cost, logistics, customs, local installer cost, spare parts cost, warranty reserve, gross profit, gross margin, first-year profit, annual recurring profit, 3-year LTV and 5-year LTV.

Add AMC module:
Basic AMC, Compliance AMC, Commercial AMC, Premium AMC.
Support percentage-based fee, point-based fee, site-based fee and service-level-based fee.
Allow annual maintenance fee to be calculated as 5%-25% of project value depending on solution line.

Add warranty module:
Separate Supplier Warranty and Customer Warranty.
Supplier warranty records warranty years, repair/replacement policy, shipping responsibility, response time and spare parts support.
Customer warranty supports pass-through warranty, managed warranty, fast replacement plan and premium AMC.
Make clear that AinerWise provides system-level support, while hardware warranty follows supplier policy unless customer purchases managed warranty or fast replacement.

Add spare parts inventory:
Track spare parts by project, product, quantity, location, reserved stock, reorder level, expiry date and cost.
Add recommended spare parts reserve as part of quotes.
Support spare parts kit, AinerWise shared spare pool and fast replacement plan.

Add maintenance and calibration:
Maintenance schedules, calibration records, probe replacement, battery replacement, firmware update, annual inspection, report review.
Show upcoming maintenance and renewal dates in buyer portal and admin dashboard.

Add ticket system:
Customers can report device failure, alarm issue, network issue, report issue, calibration request, on-site service and expansion request.
Each ticket should know whether it is covered by warranty, AMC or paid service.

Add buyer portal pages:
Project Overview, Site Data, Files, AI Assessment, Proposal Plans, BOM Sheet, Finance Summary, AMC Plan, Warranty, Tickets, Reports, Messages and Timeline.

Add admin dashboard:
High LTV leads, project margin, ARR, AMC renewals, warranty expiries, calibration due, probe replacement due, open tickets, low spare parts stock and gross profit.

Add Telegram notifications:
High LTV Lead, Phase-1 Requested, Quote Approved, Contract Signed, Payment Due, AMC Renewal Due, Warranty Expiring, Calibration Due, Probe Replacement Due, Ticket Opened, Supplier Warranty Claim Needed.

Important business rule:
Do not expose raw product model and supplier cost on the public website. Customers see solution packages, monitoring points and service plans. Admin sees real product model, supplier cost, margin and warranty policy.

AinerWise should be a lifecycle service platform, not a one-time device shop.
```

---

# 15. 最终建议

你最好不要完全把售后责任甩给供应商，也不要自己无条件包所有硬件。

最佳方案是：

```text
客户面对 AinerWise。
AinerWise 做系统级服务和支持协调。
硬件本体默认按供应商质保。
客户如想省心，可以购买 Managed Warranty / Fast Replacement / Premium AMC。
报价里必须加入备件预留和维护费用。
```

这样你既有长期饭票，又不会被售后拖死。

