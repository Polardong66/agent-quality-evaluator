# Agent Quality Evaluator (OPI Framework)

高代码 Agent 系统质量评估技能，基于 OPI（Output-Process-Input）三层分析框架，从性能维度和商业维度共六大评估轴对 Agent 系统进行结构化评分。

## 快速开始

在 WorkBuddy 中通过对话触发，或直接运行评估脚本：

```bash
python3 scripts/evaluate.py \
  --scores '{"accuracy":85,"stability":70,"speed":60,"controllability":75,"cost":80,"compliance":55}' \
  --preset "通用场景"
```

## 六大评估轴

| 维度 | 评估轴 | 权重（通用） |
|------|--------|:----:|
| 性能 | 准确性 | 25% |
| 性能 | 稳定性 | 25% |
| 性能 | 响应速度 | 15% |
| 商业 | 可控性 | 10% |
| 商业 | 成本 | 15% |
| 商业 | 合规性 | 10% |

三种预设：通用场景 / 受监管行业（金融/法律/医疗） / 实时服务（ChatBot/在线客服）

## 特性

- **6 步评估流程**，每步有 🔴 CHECKPOINT 用户确认
- **3 种权重预设** + 自定义权重
- **5 级成熟度模型**（L1 实验原型 → L5 AI 原生）
- **7 个 APM 管控点**评估（规划/记忆/工具/行动/编排/安全/可观测性）
- **组件级深度评估**（路由器/收敛性/工具调用/记忆/推理/安全）
- **9 项部署前门禁**检查
- **11 条评估者反例黑名单**
- **持续评估飞轮** + AI-CI/CD 集成建议
- **故障恢复手册**（11 条异常场景的 if-then 分支）
- **多 Agent 对比模式**

## 技能目录

```
├── SKILL.md                  # 主指令文件
├── scripts/
│   └── evaluate.py           # 评估计算脚本
├── references/
│   └── evaluation_framework.md  # 详细评分标准与权重配置
└── assets/
    └── report_template.md    # 报告输出模板
```

## 安装

```bash
# 通用安装路径
git clone https://github.com/Polardong66/agent-quality-evaluator.git /path/to/skills/agent-quality-evaluator

# 克隆到 WorkBuddy skills 目录
git clone https://github.com/Polardong66/agent-quality-evaluator.git ~/.workbuddy/skills/agent-quality-evaluator
```

## 触发词

评估Agent、Agent质量评估、Agent评分、Agent上线评审、Agent代码质量、对比Agent方案、生成质量评估报告、evaluate agent、agent quality score
