# AISLOS Experience Center — 线下体验空间架构（设计稿，Phase H/I 实施）

> 定位：不是"放了平板的商店"，而是**飞轮的物理终端** ——
> 客户体验未来 → 零售保底现金流 → 高意向项目进漏斗 → 每次对话沉淀转化数据。
> 使命句（已入宪法）：*AISLOS — Connecting Artificial Intelligence with the
> Physical World Through Real Lifecycle Experience.*
>
> 状态：**架构冻结 + EC-1 实时语音基础链路已交付**（2026-06-11）：迁移 022 落库、
> 5 个人格入 agents 注册表、`/showroom/kiosk/*` + `/admin/showroom/*` API、
> kiosk-portal 进程（4090，WebRTC 实时语音 + 工具桥 + D1 Canvas）。真实语音
> 服务商 Key、平板麦克风/回声环境与实体部署验收的开工条件 = 实体店租约签订
> （宪法第 5/10 条：没有真实用户的 Portal 不建）。本设计零依赖未建核心系统
> —— 全部挂接 Phase A–G 已交付的 Core 能力。

---

## 0. 一页结论

| 决策点 | 结论 | 理由 |
|--------|------|------|
| 终端形态 | **Web Kiosk（PWA 全屏锁定）**，不做原生 App | 一人维护；平板浏览器即运行时；MDM 锁定（iPad Guided Access / Android Fully Kiosk） |
| 语音方案 | **实时 speech-to-speech API + 工具桥接 Core**（方案 A）；组合管线（STT→consult→TTS）为降级备选（方案 B） | 门店要的是 <1s 往返和打断能力；数据真实性靠工具调用保证，不靠模型记忆 |
| 右屏演示 | **确定性 Presentation Canvas**（工具驱动的预制组件）为主；Browser-Agent 实时操作降为 R&D 档 | 零售现场容不下抽卡式的演示失败；确定性组件给出同样的"看 AI 干活"效果 |
| 五个平板 | = **agents 注册表的五个新人格**，复用 require_agent 授权门 + agent_slug 归属 | Phase G 地基直接吃到；每台平板一个数字员工，Console 里统一管 |
| 店内下单 | Store 模块上线前走 **Showroom Order 过渡流**（库存预留 + 店内刷卡 + 账本记账） | 不等电商全量；不碰线上支付牌照问题 |
| 数据资产 | **showroom_sessions 转化数据集**（预算/国家/需求/最终购买） | Rule #1 的直接兑现 —— 这是别人复制不了的实体转化数据 |

---

## 1. 总体架构（零新核心系统）

```
┌─ 店内 ──────────────────────────────────────────────┐
│  平板 ×5（Web Kiosk，全屏 PWA，MDM 锁定）             │
│  ┌─────────────┬──────────────────────┐             │
│  │ 左：语音对话 │ 右：Presentation     │  实物货架    │
│  │ 波形/字幕/   │ Canvas（产品对比/    │  ←AI 指引   │
│  │ AI 身份声明  │ 视频/案例/报价/库存） │  店主取实物  │
│  └─────────────┴──────────────────────┘             │
└──────────┬───────────────────────────────────────────┘
           │ WebRTC（语音流）+ HTTPS（工具/渲染指令）
┌──────────▼───────────────────────────────────────────┐
│ Ainerwise Core realtime gateway（现由 Core API 承载）    │
│  /showroom/kiosk/voice-config 签发临时凭证、注入工具表   │
│  /showroom/kiosk/realtime-tool-call：设备 + Agent 授权门 │
│            → 检索/比价/库存/案例/下单草稿/屏幕渲染指令 │
│  转写落 ai.conversations(channel='showroom')          │
├──────────────────────────────────────────────────────┤
│ Ainerwise Core（不变）：products/pricing/inventory/    │
│ cases/knowledge/leads/agents/grants/ledger/events     │
└──────────────────────────────────────────────────────┘
           │
   语音模型服务商（realtime speech-to-speech，多语言）
```

原则：**平板是哑终端**。所有数据、授权、审计在服务端；语音模型只负责听说，
事实全部来自工具调用（产品库/价格/库存/案例），杜绝幻觉报价。

## 2. 终端层（Kiosk）

- **第 10 个 Portal 进程**：按冻结的 Portal 模式（独立进程/URL/路由白名单，
  复用 3 套 Nuxt 基座之一）—— Kiosk 复用 `frontend-h5` 基座新增 kiosk 布局，
  独立进程跑 4090 端口，挂同一个 Core API，绝不复制数据层。
  单页双栏布局 + 待机吸引屏（attract loop：案例轮播）。
- **设备身份**：`kiosk_devices` 注册（见 §8），设备 token（非用户 JWT），
  开机自动认领人设 Agent、门店、默认语言。
- **唤醒交互**：触摸"开始对话/Start"按钮唤醒（**不做常开麦克风** ——
  合规 + 省钱）；90 秒无语音自动结束会话回待机。
- **语言**：首屏旗帜选择 sr/en/zh/pl/de，或开口自动识别后切换。
- **离线容错**：产品目录与案例做本地缓存（Service Worker），断网时降级为
  可浏览目录 + "请呼叫店主"。
- 硬件建议：10-13" 平板 + 指向性麦克风 + 立式支架；iPad 走 Guided Access，
  Android 走 Fully Kiosk Browser；统一 MDM 管理远程更新。

## 3. 语音管线（核心选型）

**方案 A（主选）：实时 speech-to-speech + Core 工具桥**

```
平板麦克风 → WebRTC → 语音模型实时会话
                        │ 函数调用（tool calls）
                        ▼
        Core /showroom/kiosk/realtime-tool-call
        require_agent(slug, scopes, workflow='showroom')  ← Phase G 授权门
        ├─ search_products(query, category)       [product_data]
        ├─ compare_products(ids)                  [product_data]   差异表
        ├─ check_stock(product_id)                [product_data]   本店/仓库
        ├─ find_similar_cases(area, budget, type) [project_data]   已有引擎
        ├─ get_install_guide(product_id)          知识库 RAG（已有）
        ├─ create_showroom_order(items)           [quotes]  草稿，店主确认
        ├─ create_lead(contact, need)             [customer_data] 既有 internal API
        └─ show_on_screen(view, payload)          右屏渲染指令（§4）
```

- 会话凭证：平板 → Core `/showroom/kiosk/voice-config`（设备 token 鉴权）→
  签发语音服务商临时密钥 + 注入人设 system prompt（agents.config_json：
  名字/性格/语气/语言）+ 工具 schema。**长期密钥永不下发到平板。**
- EC-1 已开放并接入 `search_products`、`compare_products`、`check_stock`、
  `show_on_screen`；案例、RAG、订单草稿和 Lead 创建继续按门店验收顺序开放。
- 转写双轨落库：每轮 user/assistant 文本写 `ai.messages`
  （conversation.channel='showroom'），与网页聊天同一数据模型 —— 记忆、
  审核、统计全部复用。
- 延迟预算：唤醒→首响 <1.2s；工具调用轮 <2.5s（工具执行在 Core 本地，
  数据库查询 <50ms，瓶颈只在语音模型）。
- **方案 B（降级备选/成本敏感模式）**：浏览器流式 STT → 既有 consult
  workflow → TTS。延迟 2-3s，但完全复用现有管线、成本减半。Kiosk 配置项
  可按店切换 A/B。

## 4. 右屏演示层（三档，按可靠性排序）

| 档 | 形态 | 时机 |
|----|------|------|
| **D1 确定性 Canvas（主力）** | `show_on_screen` 工具驱动预制 Vue 组件：产品卡/三型号对比表/安装视频/案例画廊（相似度标注）/报价摘要/库存卡（本店 2 件·仓库 15 件）/二维码（带走链接） | 开业即有 |
| D2 引导式 Web | Canvas 内嵌真实官网页（insights/案例页），按工具指令滚动定位高亮 | v1.5 |
| D3 生成式/3D/Browser-Agent | 客户上传房间照片 → ai_media 生成智能化改造效果图（Image Studio 已有管线）；Agent Team 会议视图（Phase H 编排就绪后）；browser-agent 实时操作 = R&D 展示位 | Phase I |

工程判断（写进设计的诚实条款）：**Browser-Agent 现场实时操作演示效果惊艳但
失败率高，零售环境第一原则是"永远不在客户面前卡住"** —— D1 用结构化工具
调用渲染同样制造"看 AI 干活"的体验，且 100% 确定性。D3 保留为吸引眼球的
展示位，不承担成交动线。

## 5. 五个人格平板 = 五个数字员工（复用 Phase G）

```
agents 表新增五行（vendor='official'，showroom 专属 workflows）：
  smart-home-expert   智能家居专家   亲切耐心，面向 DIY 改造客户
  solar-expert        光伏专家       数据型，讲回本周期
  security-expert     安防专家       严谨，讲法规与案例
  shopping-assistant  导购助理       高效，比价+库存+下单
  design-consultant   设计顾问       视觉型，主打 D3 效果图
```

- 每台平板绑定一个 slug；人设（语气/声线/头像/开场白）= `config_json`，
  Agent Console 现有页面直接管理（暂停一台平板 = paused 一个员工）。
- 授权各异：shopping-assistant 有 `quotes`；design-consultant 有 `ads`
  （生成效果图）；都没有 `payment`（宪法第 9 条：高风险动作不可调用）。
- 每次会话 `agent_runs.agent_slug` 归属 → Console 看每台平板的接待量/
  token 成本/转化，跟其他员工同一张报表。

## 6. 店内成交流（Store 模块上线前的过渡设计）

```
客户："这个电动阀门和那个有什么区别？"
AI：compare_products → 右屏对比表 → check_stock → "本店有 2 件"
客户："要一个。"
AI：create_showroom_order（草稿）→ 右屏订单摘要 + 取货码
店主：柜台扫码确认 → 刷卡机收款（线下 POS，不碰线上支付）
系统：库存扣减（InventoryItem/StockMovement 已有）
      + 账本分录（bank:pos_store → platform:revenue，复式记账已有）
      + 会话标记 outcome='purchase'
高意向项目客户：AI 主动收集联系方式 → create_lead → 你接手 → 既有总承包主循环
```

Ainerwise Store（电商模块）上线后，showroom_orders 并入正式订单流，
此过渡流退役 —— 设计上 showroom_orders 字段与未来 Store orders 对齐。

## 7. 数据飞轮（Rule #1 兑现点）

每次会话沉淀一条 `showroom_sessions`：
设备/人格/语言/时长/需求类目/预算区间/对比过的产品/**outcome
（purchase|lead|browse）**/订单或 lead 关联。一年 × 5 台 × 日均 20 会话 ≈
**3.6 万条带真实购买结果的本地化需求数据** —— 训练导购 Agent、选品、
定价、广告投放全部吃这个数据集。网页聊天 + 电话（Voice adapter）+ 门店
三个渠道共用 ai.conversations，渠道字段区分，分析口径统一。

## 8. 数据模型（设计稿，开工时建迁移）

```sql
stores (id, region_id FK, name, address, city, country, timezone, status)

kiosk_devices (
  id, store_id FK, name,                 -- "门口左 1 号机"
  device_token_hash,                     -- 设备凭证（可吊销）
  agent_slug FK agents.slug,             -- 绑定人格
  default_lang, voice_mode,              -- 'realtime' | 'pipeline'（方案A/B）
  status, last_seen_at
)

showroom_sessions (
  id, device_id FK, conversation_id FK ai.conversations,
  lang, started_at, ended_at,
  need_category, budget_hint NUMERIC NULL,
  products_viewed_json,
  outcome,                               -- purchase|lead|browse|abandoned
  order_id FK NULL, lead_id FK NULL
)

showroom_orders (
  id, session_id FK, store_id FK,
  items_json,                            -- [{product_id, qty, unit_price}]
  total NUMERIC(12,2), currency,
  status,                                -- draft|confirmed|paid_in_store|cancelled
  pickup_code, confirmed_by FK users NULL
)
```

orchestrator 新增：`/realtime/session`、`/realtime/tool-call`（设备 token +
require_agent 双重校验）。**无新进程** —— realtime broker 是 orchestrator
的新端点组。

## 9. 合规与安全（开业前置检查单）

- **AI Act Art.50**：屏幕常驻"You are talking to an AI assistant"声明 +
  开场白自报身份（写死在人设模板，不可被 config 覆盖）。
- **GDPR**：按钮唤醒、不做常开监听；不录音频原始流，只存文本转写；
  店内告示牌声明数据用途；转写保留期与删除策略入数据清单；
  **不做人脸/生物识别**（宪法 Rule #1 合规细则）。
- 设备安全：kiosk token 只能调 showroom 工具集；admin/内部 API 物理不可达；
  单设备限流 + 每会话 token 预算上限（防滥用，也是成本闸门）。
- 成本模型：方案 A 语音 ≈ €0.06-0.20/分钟 → 单会话(8min) €0.5-1.6；
  日均 20 会话/台 × 5 台 ≈ €50-160/天封顶预算，broker 层硬性限额 +
  低峰自动切方案 B。

## 10. 实施分期

```
EC-0 试点（店租签订即启动，~3 周）
  1 台平板 · 方案A语音 · D1 Canvas（产品对比/库存/案例/订单草稿）
  showroom 表迁移 · shopping-assistant 人格 · 店内 POS 过渡流
EC-1 全量（试点跑通 2 周后）
  5 台 × 5 人格 · D2 引导式 Web · 周报进 Business Brain（门店转化指标）
EC-2 体验升级（Phase H 能力就绪后）
  房间照片→效果图（D3）· Agent Team 会议视图 · Project Space 现场开通
依赖清单：店面租约 · 平板硬件×5 + 支架 + 麦克风 · 语音 API key ·
          POS 刷卡机 · 店内合规告示
```

## 11. 防腐条款（本 Portal 专属）

- ❌ 原生 App（Web Kiosk 足够，违反则维护成本翻倍）
- ❌ 常开麦克风 / 人脸识别 / 客流摄像分析
- ❌ 平板持有长期密钥或直连数据库
- ❌ Browser-Agent 承担成交动线（只做 R&D 展示位）
- ❌ 店内自建支付（POS 刷卡 + 账本记账，线上支付等 Store + PSP）
- ❌ 语音无预算上限运行
