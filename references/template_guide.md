# report_template.html 占位符填充指南

## 使用方式

评估时直接复制 `assets/report_template.html`，替换所有 `{{...}}` 占位符后输出为最终报告。

## 占位符清单与填充规则

### Section 1 — 报告头

| 占位符 | 填充规则 | 示例 |
|--------|---------|------|
| `{{ICON}}` | 项目对应 emoji，无合适选 🧠 | 🍽️ |
| `{{AGENT_NAME}}` | Agent 系统名称 | 饮食分析记录智能体 |
| `{{DATE}}` | 评估日期 YYYY-MM-DD | 2026-06-23 |
| `{{PROJECT}}` | 项目目录名 | food_analysis_agent_python |
| `{{SCENARIO}}` | 场景名称（通用场景/受监管行业/实时服务/自定义） | 通用场景 |
| `{{TOTAL_SCORE}}` | 加权总分，保留 1 位小数 | 60.1 |
| `{{SCORE_COLOR}}` | 得分颜色：≥80=#00b894, ≥60=#fdcb6e, <60=#d63031 | #fdcb6e |
| `{{GRADE}}` | 等级：A(≥90) / B+(≥80) / B(≥70) / C+(≥60) / C(≥50) / D(<50) | C+ |
| `{{MATURITY}}` | 成熟度等级 L1-L5：L1(0-39) L2(40-54) L3(55-69) L4(70-84) L5(85-100) | L3 |

### Section 2 — 评估概览

`{{SUMMARY_ITEMS}}` — 6 个 summary-item，格式：
```html
<div class="summary-item"><div class="num">3</div><div class="lbl">Agent 数量</div></div>
```
建议项目：Agent 数量、交付形态、Prompt 总行数、P0 数量、P1 数量、P2 数量。

### Section 3 — 图表

`{{SCORES_JSON}}` — 六维度得分数组，索引顺序固定（不可调换）：
```
[准确性, 稳定性, 响应速度, 可控性, 成本, 合规性]
```
示例：`{{SCORES_JSON}}` → `[70, 65, 60, 58, 50, 40]`

### Section 4 — 维度得分明细

`{{SCORE_BARS}}` — 6 个 score-item，格式：
```html
<div class="score-item">
  <span class="score-label">准确性</span>
  <div class="score-bar-bg"><div class="score-bar-fill" style="width:70%;background:linear-gradient(90deg,#0984e3,#74b9ff)"><span>70</span></div></div>
  <span class="score-value" style="color:#0984e3">70</span>
  <span class="dim-weight">权重 25%</span>
</div>
```
颜色规则：≥75 用蓝色系、60-74 用橙色系、<60 用红色系。

### Section 5 — 逐维度深度评估

`{{DIMENSION_CARDS}}` — 6 个 dim-card，按准确性→稳定性→响应速度→可控性→成本→合规性顺序。

```html
<div class="dim-card good">   <!-- good(≥75) / warn(60-74) / bad(<60) -->
  <div class="dim-header">
    <h3>1. 准确性（Accuracy）</h3>
    <div>
      <span class="dim-score-num" style="color:#0984e3">70</span>
      <span style="font-size:12px;color:#636e72">/100 · 权重 25%</span>
    </div>
  </div>
  <div class="evidence">
    <strong>✅ 优势：</strong>
    <ul>
      <li>具体优势 1</li>
      <li>具体优势 2</li>  <!-- 至少 2 条 -->
    </ul>
    <strong>❌ 缺陷：</strong>
    <ul>
      <li>具体缺陷 1</li>
      <li>具体缺陷 2</li>  <!-- 至少 2 条 -->
    </ul>
  </div>
</div>
```

缺陷中如需标注优先级使用 `.tag`：
```html
<li><span class="tag bad">P0</span> 缺陷描述</li>
```

### Section 6 — APM 管控点

`{{APM_ROWS}}` — 7 个 apm-table 行，顺序固定：
1. 参数提取准确性 · 2. 工具调用鲁棒性 · 3. 错误恢复机制
4. 上下文管理 · 5. 输出格式一致性 · 6. 安全护栏 · 7. 可观测性

```html
<tr><td class="apm-pass">✅</td><td>参数提取准确性</td><td>说明文字</td></tr>
```
状态类：`apm-pass`(✅) / `apm-warn`(⚠️) / `apm-fail`(❌)

### Section 7 — 改进建议表

`{{IMPROVEMENT_ROWS}}` — 所有改进项，P0 优先，同类内按损失分降序。

```html
<tr>
  <td><span class="priority-p0">P0 🔴</span></td>
  <td>合规性</td>
  <td>具体问题描述（含文件路径:行号）</td>
  <td>可执行的改进方案</td>
  <td>预期收益</td>
</tr>
```

### Section 8 — 系统架构

`{{ARCHITECTURE}}` — 文本流程图。**所有 Agent 名称必须使用中文释义**，禁止使用英文类名：

```html
<div class="arch-flow">
  <div class="arch-node">📷 图片输入</div>
  <span class="arch-arrow">→</span>
  <div class="arch-node">Agent 1<br>食物图片识别</div>
  <span class="arch-arrow">→</span>
  <div class="arch-node">Agent 2<br>营养标准计算</div>
  <span class="arch-arrow">→</span>
  <div class="arch-node" style="background:#00b894">📊 Markdown 报告</div>
</div>
<div style="text-align:center;margin-top:12px;font-size:12px;color:#636e72">
  模型/框架/依赖说明（中文描述）
</div>
```

> 规则：节点文字只用中文 + emoji，不出现英文类名（如 FoodRecognitionAgent）。技术栈说明也优先中文描述。

## 禁止行为

- ❌ 调整 9 个 Section 的顺序
- ❌ 修改 CSS 变量值或删除样式规则
- ❌ 将雷达图/柱状图替换为其他图表类型
- ❌ 遗漏任一 Section（即使数据不足也要标注「数据不足」）
- ❌ 非 HTML 格式输出（禁止纯 Markdown 替代）
