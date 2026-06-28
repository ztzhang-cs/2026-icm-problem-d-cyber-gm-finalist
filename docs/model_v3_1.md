# 2026 ICM Problem D: Cyber-GM V3.1 完整模型说明书
## 宏观动力学、明星价值与多渠道决策模型 (PDF 打印优化版)

---

## 1. 模型架构概览 (System Architecture)

**设计原则：**
本模型严格遵循 Cyber-GM V2 的 **"预测 (Prediction) -> 优化 (Optimization) -> 决策 (Decision)"** 闭环结构，并在 V3 基础上扩展了“资产获取”与“系统性冲击应对”层。

**核心升级：**
* **输入层扩展：** 引入宏观经济状态向量 $\mathbf{M}_t$ 和社交媒体情绪数据。
* **中间层增强：** 新增 **MSM** (宏观敏感度)、**SPVE** (明星价值)、**DAM** (多渠道获取) 和 **ERM** (扩军响应)。
* **决策层修正：** 引入动态资本成本 $WACC_t$ 作为风险贴现因子，并将扩军与位置风险纳入 MDP 状态空间。

---

## 2. 模块一：宏观经济敏感度模块 (MSM)
**目标：** 量化外部经济环境（通胀、利率、收入）对球队财务底线的冲击。

### 2.1 需求侧：收入弹性修正的门票需求模型
引入消费者购买力平价概念，修正基础需求曲线：

$$
\ln(q_{g,t}) = \alpha + \beta_p \ln\left(\frac{P_{g,t}}{CPI_t}\right) + \beta_I \ln(Y_{MSA,t}) + \beta_{U} U_{t} + \gamma \mathbf{X}_{game} + \epsilon_t
$$

**变量定义：**
* $q_{g,t}$：比赛 $g$ 的上座率（$0 \le q \le 1$）。
* $P_{g,t} / CPI_t$：**实际票价**（剔除通胀因素）。
* $Y_{MSA,t}$：球队所在城市人均可支配收入（收入弹性 $\beta_I > 0$）。
* $U_{t}$：区域失业率（反映经济衰退滞后打击）。

### 2.2 供给侧：运营成本通胀指数 (SOCI)
构建体育专用通胀指数，用于预测未来成本：

$$
SOCI_t = w_{E} I_{E}(t) + w_{L} I_{L}(t) + w_{S} CPI_{S}(t)
$$

**变量定义：**
* $I_{E}$：能源价格指数（影响包机/场馆运营）。
* $I_{L}$：劳资协议工资增长指数。
* $w$：各项权重。

**修正后的单场利润公式：**
$$
\Pi_g = (P_g q_g + R_{aux}) - C_{base} \left( \frac{SOCI_t}{SOCI_{0}} \right)
$$

### 2.3 金融侧：动态 WACC 杠杆模型
采用动态加权平均资本成本（WACC）作为全模型的折现率：

$$
WACC_t = \frac{E}{V} R_e(t) + \frac{D}{V} R_d(t) (1 - \tau)
$$

* **决策约束：** 当投资回报率 $ROIC < WACC_t$ 时，强制触发“去杠杆”动作。

---

## 3. 模块二：明星选手价值评估引擎 (SPVE)
**目标：** 解决 Problem D 中“球员价值基于人气而非胜场”的难题。

### 3.1 综合商业价值公式
将球员 $i$ 的总价值 $V_i$ 分解为竞技价值与商业价值：

$$
V_i = \underbrace{w_1 \cdot WS_i}_{\text{竞技(Wins)}} + \underbrace{w_2 \cdot (SMV_i + Ext_i)}_{\text{商业(Profit)}}
$$

### 3.2 组件 A：社交媒体价值 (SMV)
$$
SMV_i = \sum_{k \in \text{platforms}} \left( F_{i,k} \cdot E_{i,k} \cdot CPE_k \right) \cdot \lambda_{fit}
$$
* $F_{i,k}$：粉丝数；$E_{i,k}$：互动率；$CPE_k$：单次互动成本。

### 3.3 组件 B：票房引力与“客场外部性”
$$
Ext_i = \delta_{H} \Delta A_{home} + \delta_{V} \Delta A_{visit} \cdot \theta_{share}
$$
* 量化球星在客场带来的上座率提升（$\Delta A_{visit}$）及联盟分红（$\theta_{share}$）。

### 3.4 蜜月期衰减函数 (Novelty Decay)

明星效应随时间的衰减模型：

$$
B_t = B_{0} \cdot e^{-\lambda t}
$$

* $B_t$：$t$ 时刻的票房提升力。
* $\lambda$：衰减常数。网红型球员 $\lambda$ 较高，实力型巨星 $\lambda$ 较低。

---

## 4. 模块三：多渠道资产配置 (DAM)
**目标：** 响应 Problem D 关于 "Draft, Free Agency, Trades" 的决策要求。我们将球员获取视为在 $WACC_t$ 约束下的**投资组合优化问题**。

### 4.1 渠道净现值 (NPV) 量化

#### A. 选秀 (The Draft) - 高波动长线投资
$$
NPV_{draft, i} = \sum_{t=1}^{T_{ctrl}} \frac{\mathbb{E}[V_i(t)] - Salary_{rookie}(t)}{(1 + WACC_t)^t} - Cost_{scout}
$$
* **逻辑：** 当宏观利率 ($WACC_t$) 上升时，未来现金流折现率变高，模型会自动降低对“需长期培养的新秀”的估值。

#### B. 自由球员 (Free Agency) - 通胀敏感型投资
$$
NPV_{FA, i} = \sum_{t=1}^{T_{con}} \frac{V_i(t) - Salary_{ask, i} \cdot (1 + \pi_{inflation})^t}{(1 + WACC_t)^t}
$$
* $\pi_{inflation}$：由模块一 $SOCI_t$ 预测的薪资通胀率。若预测通胀飙升，模型倾向于锁定长约。

#### C. 交易 (Trade) - 资产置换
$$
NPV_{trade, i} = NPV_{FA, i} - \left( \sum_{j \in Out} V_j + \text{Val}(Picks) \right)
$$

### 4.2 投资组合优化 (Portfolio Optimization)
$$
\text{Maximize } J = \sum_{i,c} x_{i,c} \cdot NPV_{i,c}
$$
**约束条件：**
1.  **工资帽：** $\sum Salary < Cap_{limit}$
2.  **结构性约束：** $N_{veterans} \ge K$ (强制保留老将以降低更衣室风险，继承自 V2)。

---

## 5. 模块四：联盟扩军响应机制 (ERM)
**目标：** 响应 Problem D 关于 "League Expansion" 及 "New Team Location" 的影响。

### 5.1 扩军保护优化算法 (Expansion Protection)
当联盟扩军时，基于 **V3 的 SPVE 值** 而非单纯胜率来制定保护名单 $P$：

$$
\text{Maximize } \quad \Omega = \sum_{i \in P} \left( w_1 \cdot WS_i + w_2 \cdot SMV_i \right)
$$
$$
\text{s.t.} \quad |P| \le k_{limit}
$$
* **关键差异：** 如果某球员胜率贡献一般，但 $SMV$ (网红指数) 极高，模型会强制保护，防止商业价值流失。

### 5.2 新球队位置引力模型 (Location Gravity Model)
量化新球队对现有市场份额的稀释风险：

$$
\text{Risk}_{dilution} = \theta \cdot \frac{Pop_{new} \cdot GDP_{new}}{Distance(Team_{us}, Team_{new})^\alpha}
$$
* **Case A (远距离大城市):** 稀释全国转播合同，增加差旅成本 ($SOCI$ 上升)。

* **Case B (近距离城市):** 直接抢夺季票用户。策略调整：降低票价弹性模型中的 $P_g$ 以锁定长尾客户。

  



## 5. 新增模块五：动态票务与球迷转化策略 (Dynamic Ticket Strategy Module)

**目标：** 响应 Problem D 中关于“最大化单场收入 vs 降低票价以获取长期季票持有者”的权衡问题。本模块利用 V3 的 **MSM 需求模型** 确定最优定价 $P_g^*$。

### 5.1 细化比赛特征向量 ($\mathbf{X}_{game}$)
为了捕捉“时间、对手人气、市场规模”等差异，我们首先细化 **模块 2.1** 中的需求协变量 $\mathbf{X}_{game}$：

$$
\mathbf{X}_{game} = [\delta_{weekend}, \delta_{holiday}, SMV_{opp}, Rank_{diff}, Month_{factor}]
$$

* $\delta_{weekend} / \delta_{holiday}$：周末与节假日虚拟变量（时间因素）。
* $SMV_{opp}$：**对手球队的明星价值** (引用模块二 SPVE)。例如对手有 Caitlin Clark 时，该值极高，推高需求曲线。
* $Rank_{diff}$：两队排名差（竞技强度）。
* $Month_{factor}$：赛季月份（通常赛季末冲刺期需求更高）。

### 5.2 定价的双重目标函数 (Dual-Objective Pricing)
Problem D 指出球队可以选择“高价高收”或“低价引流”。我们建立一个加权目标函数 $J_{price}$，结合 **即时现金流** 与 **客户终身价值 (CLV)**。

对任意一场比赛 $g$，寻找最优票价 $P_g$ 以最大化：

$$
\text{Maximize } J(P_g) = \underbrace{\left( P_g + R_{aux} \right) \cdot q_g(P_g)}_{\text{Current Cash Flow}} + \underbrace{\mu \cdot \xi_{conv} \cdot CLV_{fan} \cdot q_g(P_g)}_{\text{Future Equity Value}}
$$

**约束条件：**
$$q_g(P_g) \le Capacity_{stadium}$$

**变量定义：**
* $q_g(P_g)$：基于 **MSM (模块2.1)** 的需求预测函数。
* $R_{aux}$：场内人均二次消费（停车、餐饮、球衣）。上座率越高，这部分收入越高。
* $CLV_{fan}$：一名季票持有者的**客户终身价值** (Customer Lifetime Value)。
* $\xi_{conv}$：**转化概率** (Conversion Rate)。普通观众转化为季票持有者的概率。
* $\mu \in [0, 1]$：**战略权重系数**。
    * **$\mu \to 0$ (收割模式):** 球队处于成熟期（如卫冕冠军），追求当季利润最大化，定高价。
    * **$\mu \to 1$ (增长模式):** 球队处于重建期或扩军初期，**主动降价**以填充球馆，牺牲短期票款换取未来的季票基数。

### 5.3 季节性动态定价算法 (Season-Long Optimization)
基于上述逻辑，我们在赛季开始前对所有主场比赛进行 **分档定价 (Tiered Pricing)**：

1.  **计算基准需求得分 ($D_{score}$):**
    利用 $SOCI$ 和 $\mathbf{X}_{game}$ 预测每场比赛的基础热度。
    $$D_{score, g} = \beta_{pop} SMV_{opp} + \beta_{time} \delta_{weekend} + \dots$$

2.  **比赛分级 (Game Tiering):**
    * **Tier A (Premium):** 高 $D_{score}$ (如打强队/周末)。策略：令 $\mu=0$ (完全最大化收入)，利用低价格弹性 $\beta_p$ 提价。
    * **Tier B (Standard):** 普通比赛。策略：平衡定价。
    * **Tier C (Value):** 低 $D_{score}$ (如周二打弱队)。策略：令 $\mu=1$ (最大化上座率)，大幅降价甚至赠票，通过 $R_{aux}$ (餐饮) 和季票转化来获利。

3.  **求解最优价 $P_g^*$:**
    对目标函数求导 $\frac{\partial J}{\partial P_g} = 0$，在考虑 $Capacity$ 约束下求解。若预测上座率 $q_g > Capacity$，则提高 $P_g$ 直到 $q_g = Capacity$（撇脂定价）。

---

---

## 6. 新增模块六：危机响应与伤病管理机制 (Crisis Response & Injury Management - CRIM)

**目标：** 响应 Problem D 中关于“关键球员受伤时的管理层调整”问题。本模块不依赖直觉，而是计算“伤病冲击向量”，并自动触发财务与竞技的双重对冲策略。

### 6.1 伤病冲击量化 (Quantifying the Shock)
当关键球员 $i^*$ 在时间 $t$ 受伤，预计缺席 $T_{miss}$ 场比赛。模型首先计算**资产减值向量** $\Delta \mathbf{L}_t$：

$$
\Delta \mathbf{L}_t = \left[ \Delta WS_{team}, \Delta Rev_{ticket}, \Delta Brand \right]
$$

1.  **竞技减值 ($\Delta WS$):** 直接取该球员的 $WS_{proj}$ (预计胜场贡献) 归零。
2.  **票房减值 ($\Delta Rev$):** 调用 **模块 2 (SPVE)** 和 **模块 5 (Ticket)**。
    * 球员 $i^*$ 的缺席导致 $SMV_{team}$ (全队球星值) 下降。
    * **自动调整：** 将新的 $SMV'_{team}$ 代入票务需求函数 $q(P)$，计算维持原价情况下的预期收入损失。

### 6.2 财务对冲：保险与动态定价 (Financial Hedging)
针对 $\Delta \mathbf{L}_t$，模型生成以下财务指令：

#### A. 薪资保险激活 (Insurance Trigger)
若受伤球员薪资 $Salary_i$ 超过阈值，通常投保了短期失能险。
$$
CashFlow_{adj} = CashFlow_{raw} + \mathbb{I}(T_{miss} > 5) \cdot \eta \cdot Salary_i
$$
* $\eta$：保险赔付比例（通常为 80%）。
* **决策点：** 这笔赔付金 ($Cash$) 成为额外的“临时预算”，用于签下替代者而不触发布局硬工资帽。

#### B. 票价自动修正 (Automatic Repricing)
由于 $SMV_{team}$ 下降，需求曲线左移。为了防止上座率崩盘（影响 $R_{aux}$ 餐饮收入），模型求解新的最优价 $P^*_{new}$：
$$
P^*_{new} = \arg \max_P \left( (P + R_{aux}) \cdot q(P | SMV_{injured}) \right)
$$
* **结果：** 模型通常会建议**立即降价**或推出“且看且珍惜”的促销包，以数量弥补单价损失。

### 6.3 竞技战略枢纽：修补还是重建？ (Patch vs. Tank Pivot)
这是最关键的管理层决策。模型计算一个 **"希望指数" (Hope Index, $\mathcal{H}_t$)** 来决定赛季走向：

$$
\mathcal{H}_t = \frac{\text{Current\_Wins} + \sum_{g=t}^{End} P(Win_g | Roster_{-i^*})}{\text{Playoff\_Threshold}}
$$

* **策略 A: 激进修补 (The Patch)**
    * **触发条件：** $\mathcal{H}_t > 1.0$ (即使受伤，季后赛仍有希望)。
    * **动作：** 使用保险赔付金 $\eta \cdot Salary_i$，在 **模块 3 (DAM)** 中寻找 $NPV$ 最高、合同期短的“雇佣兵” (Rental Player) 填补空缺。
    * **目标：** 维持 $WS$，保住季后赛门票收入。

* **策略 B: 战略性放弃 (The Pivot/Tank)**
    * **触发条件：** $\mathcal{H}_t < 0.8$ (伤病导致季后赛无望)。
    * **动作：**
        1.  **停止修补：** 不签替代者，让新人上场（省钱 + 练兵）。
        2.  **资产清算：** 激活 **模块 3** 的 `Trade_Away_Bad_Contract` 动作，交易队内其他老将换取选秀权。
        3.  **长期收益：** 虽然本赛季 $\Pi_t$ 下降，但通过高顺位选秀权提升了未来的 $V_{franchise}$。

---

## 7. 综合决策层 (Cyber-GM Brain)

### 7.1 状态空间 (State Space) $S_t$
结合 V2 基础与 V3 增强变量：
$$
S_t = [\underbrace{\mathbf{M}_t, WACC_t}_{\text{宏观}}, \underbrace{F_t, L_t}_{\text{财务}}, \underbrace{Roster, \mathbf{SV}_t}_{\text{阵容与人气}}, \underbrace{Exp\_Flag, Loc_{new}}_{\text{扩军信号}}]
$$

### 7.2 动作空间 (Action Space) $A_t$
* **交易/获取：** `Draft_Heavy`, `Sign_Max_FA`, `Trade_For_Picks`
* **扩军应对：** `Protect_Core` (保核心), `Expose_Bad_Contract` (暴露垃圾合同)
* **财务/票价：** `Dynamic_Pricing`, `Deleverage` (去杠杆), `Hedging` (购买球星保险)

### 7.3 目标函数 (Objective Function)
最大化风险调整后的特许经营权价值 (Franchise Value)：

$$
V_{franchise} = \sum_{t=0}^{\infty} \gamma^t \left( \frac{\Pi_t(S,a) + \text{Valuation\_Boost}(WS_t, SMV_t)}{WACC_t} \right)
$$

---

## 8. 总结
Cyber-GM V3.1 是一个多层次的体育管理模型：
1.  **底层**利用 $SOCI$ 和 $WACC$ 捕捉宏观风险。
2.  **中层**利用 $SPVE$ 准确评估“网红球员”的真实财务价值。
3.  **顶层**通过 MDP 动态规划，在扩军、交易和日常运营中寻找“胜率”与“利润”的最佳平衡点。