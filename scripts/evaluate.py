#!/usr/bin/env python3
"""
Agent 质量评估脚本 (OPI Framework)

用法:
    python evaluate.py --config config.json
    python evaluate.py --scores '{"accuracy":85,"stability":70,"speed":60,"controllability":75,"cost":80,"compliance":50}'
    python evaluate.py --scores '{"accuracy":85,"stability":70,"speed":60,"controllability":75,"cost":80,"compliance":50}' --weights '{"accuracy":0.25,"stability":0.25,"speed":0.15,"controllability":0.10,"cost":0.15,"compliance":0.10}'
"""

import json
import sys
import os
from typing import Dict, Tuple, List

# --- 默认权重（通用场景）---
DEFAULT_WEIGHTS = {
    "accuracy": 0.25,
    "stability": 0.25,
    "speed": 0.15,
    "controllability": 0.10,
    "cost": 0.15,
    "compliance": 0.10
}

# --- 维度元信息 ---
DIMENSION_META = {
    "accuracy": {
        "name": "准确性 (Accuracy)",
        "dimension": "性能维度",
        "description": "输出内容是否正确、可信、在边缘场景下依然可靠",
        "key_checks": [
            "输出是否包含可追溯的引用/来源链接",
            "信息是否反映当前时效",
            "各部分内容深度是否均衡，论据是否充分",
            "边界场景/异常输入下的表现",
            "是否存在明显的幻觉或编造行为"
        ],
        "anti_patterns": [
            "报告没有任何引用和来源标注",
            "反思轮数一刀切，不根据主题复杂度自适应",
            "段落深度和质量参差不齐",
            "输出缺乏数据时效保障机制"
        ]
    },
    "stability": {
        "name": "稳定性 (Stability)",
        "dimension": "性能维度",
        "description": "持续运行、高并发、异常输入等场景下保持一致的预期行为",
        "key_checks": [
            "输出格式是否保持一致",
            "异常输入下是否优雅降级而非崩溃",
            "出错时中间结果是否保留",
            "Token超限是否导致崩溃",
            "不同主题/语言/规模的输入下表现是否一致"
        ],
        "anti_patterns": [
            "出错直接崩溃，中间结果全部丢失",
            "Token超限直接崩溃",
            "输出格式不稳定，需要人工二次整理",
            "无监控和告警机制"
        ]
    },
    "speed": {
        "name": "响应速度 (Response Speed)",
        "dimension": "性能维度",
        "description": "用户从请求到获得结果的全链路等待时间及进度可感知性",
        "key_checks": [
            "是否有执行进度反馈机制",
            "用户能否实时感知任务进展",
            "是否提供预计完成时间",
            "全流程是否可观测",
            "是否有超时控制和降级策略"
        ],
        "anti_patterns": [
            "执行过程完全不透明",
            "无任何进度指示或中间状态反馈",
            "无超时控制导致长时间无响应"
        ]
    },
    "controllability": {
        "name": "可控性 (Controllability)",
        "dimension": "商业维度",
        "description": "Agent行为是否在预期范围内，触及业务边界时是否有干预机制",
        "key_checks": [
            "是否对输入进行预检",
            "非业务相关的输入是否有明确拒绝提示",
            "执行过程中是否有干预入口",
            "是否支持回滚或撤销操作",
            "系统行为的可解释性和可审计性"
        ],
        "anti_patterns": [
            "无输入校验，用户输入带来不确定性",
            "异常输入直到执行失败才暴露",
            "缺乏可中断/可干预的机制"
        ]
    },
    "cost": {
        "name": "成本 (Cost)",
        "dimension": "商业维度",
        "description": "每次推理的Token消耗和工具调用费用是否在可接受的业务范围内",
        "key_checks": [
            "单次任务Token消耗是否可预估",
            "是否有执行循环终止保护",
            "是否有上下文管理机制",
            "工具调用次数是否合理",
            "成本是否随输入规模线性可预期"
        ],
        "anti_patterns": [
            "执行循环没有终止保护，Token失控",
            "没有上下文管理，Token线性增长",
            "反思/重试循环没有上限控制"
        ]
    },
    "compliance": {
        "name": "合规性 (Compliance)",
        "dimension": "商业维度",
        "description": "输出是否满足业务场景的合规要求",
        "key_checks": [
            "关键结论是否有可追溯的来源链接",
            "内容是否来源于公开/授权信息",
            "是否涉及内部敏感数据",
            "输出是否包含免责声明",
            "是否符合特定行业监管要求"
        ],
        "anti_patterns": [
            "报告无引用和来源标注",
            "内容来源不明，无法追溯",
            "缺乏合规审查机制"
        ]
    }
}

# --- 权重预设 ---
WEIGHT_PRESETS = {
    "通用场景": DEFAULT_WEIGHTS,
    "受监管行业（金融/法律/医疗）": {
        "accuracy": 0.20, "stability": 0.20, "speed": 0.10,
        "controllability": 0.15, "cost": 0.10, "compliance": 0.25
    },
    "实时服务（ChatBot/在线客服）": {
        "accuracy": 0.20, "stability": 0.25, "speed": 0.25,
        "controllability": 0.10, "cost": 0.10, "compliance": 0.10
    }
}


def get_grade(score: float) -> Tuple[str, str]:
    """根据总分返回等级和含义"""
    if score >= 85:
        return "A (优秀)", "系统质量高，可直接上线使用"
    elif score >= 70:
        return "B (良好)", "系统整体可用，建议优化几个短板后上线"
    elif score >= 55:
        return "C (及格)", "系统基本可用，但存在明显短板需改进"
    elif score >= 40:
        return "D (较差)", "系统存在严重问题，需大幅改进后重新评估"
    else:
        return "E (不合格)", "系统质量不达标，需重构"


def get_dimension_grade(score: float) -> str:
    """返回单维度等级"""
    if score >= 90:
        return "优秀"
    elif score >= 75:
        return "良好"
    elif score >= 60:
        return "及格"
    elif score >= 40:
        return "较差"
    else:
        return "不合格"


def get_improvement_suggestions(scores: Dict[str, float], 
                                  weights: Dict[str, float]) -> List[Dict]:
    """生成改进建议，按(权重 × 损失分)排序"""
    suggestions = []
    for dim_key, dim_meta in DIMENSION_META.items():
        score = scores.get(dim_key, 0)
        weight = weights.get(dim_key, 0)
        loss = (100 - score) * weight  # 加权损失分

        if score >= 85:
            priority = "低"
        elif score >= 70:
            priority = "中"
        else:
            priority = "高"

        dim_suggestions = []
        # 根据得分生成针对性建议
        if score < 60:
            dim_suggestions.append(f"该维度得分较低，建议优先解决核心问题")
            for ap in dim_meta["anti_patterns"]:
                dim_suggestions.append(f"⚠️ 需检查: {ap}")
        elif score < 75:
            dim_suggestions.append(f"该维度存在改进空间")
            dim_suggestions.append(f"建议逐一排查以下检查点: {'; '.join(dim_meta['key_checks'][:3])}")
        elif score < 85:
            dim_suggestions.append(f"该维度表现尚可，可针对细节优化")
        else:
            dim_suggestions.append(f"该维度表现优秀，保持即可")

        suggestions.append({
            "dimension": dim_key,
            "name": dim_meta["name"],
            "score": score,
            "weight": weight,
            "weighted_loss": round(loss, 1),
            "priority": priority,
            "suggestions": dim_suggestions
        })

    # 按加权损失分降序排列
    suggestions.sort(key=lambda x: x["weighted_loss"], reverse=True)
    return suggestions


def get_apm_assessment(scores: Dict[str, float]) -> Dict[str, str]:
    """根据评分推断APM管控点状态"""
    apm = {}

    # 规划控制 (Planning Control) — 关联准确性和可控性
    plan_avg = (scores.get("accuracy", 0) + scores.get("controllability", 0)) / 2
    if plan_avg >= 80:
        apm["规划控制"] = "✅ 良好 — 任务拆解合理，步骤清晰，意图识别准确"
    elif plan_avg >= 60:
        apm["规划控制"] = "⚠️ 需改进 — 存在步骤冗余或拆解不够精准的情况"
    else:
        apm["规划控制"] = "❌ 薄弱 — 任务规划和意图识别存在明显缺陷"

    # 记忆控制 (Memory Control) — 关联成本、稳定性和可控性
    mem_avg = (scores.get("cost", 0) + scores.get("stability", 0) + scores.get("controllability", 0)) / 3
    if mem_avg >= 80:
        apm["记忆控制"] = "✅ 良好 — 上下文管理合理，信息生命周期管控得当"
    elif mem_avg >= 60:
        apm["记忆控制"] = "⚠️ 需改进 — 可能存在过量或不足的上下文管理"
    else:
        apm["记忆控制"] = "❌ 薄弱 — 上下文管理失控，Token浪费严重"

    # 工具控制 (Tool Control) — 关联稳定性、成本和准确性
    tool_avg = (scores.get("stability", 0) + scores.get("cost", 0) + scores.get("accuracy", 0)) / 3
    if tool_avg >= 80:
        apm["工具控制"] = "✅ 良好 — 工具选择精准，调用时机合理，错误恢复可靠"
    elif tool_avg >= 60:
        apm["工具控制"] = "⚠️ 需改进 — 存在冗余调用或错误恢复不完善的情况"
    else:
        apm["工具控制"] = "❌ 薄弱 — 工具使用效率低，错误处理不足"

    # 行动控制 (Action Control) — 关联准确性和合规性
    action_avg = (scores.get("accuracy", 0) + scores.get("compliance", 0)) / 2
    if action_avg >= 80:
        apm["行动控制"] = "✅ 良好 — 输出格式稳定，内容边界清晰，结果可直接使用"
    elif action_avg >= 60:
        apm["行动控制"] = "⚠️ 需改进 — 输出格式偶有波动或内容边界不够明确"
    else:
        apm["行动控制"] = "❌ 薄弱 — 输出不可控，格式混乱或内容越界"

    # 编排控制 (Orchestration Control) — 关联可控性、响应速度和准确性
    orch_avg = (scores.get("controllability", 0) + scores.get("speed", 0) + scores.get("accuracy", 0)) / 3
    if orch_avg >= 80:
        apm["编排控制"] = "✅ 良好 — 子任务分配合理，收敛路径清晰，无冗余迭代"
    elif orch_avg >= 60:
        apm["编排控制"] = "⚠️ 需改进 — 存在部分冗余迭代或收敛性不足的情况"
    else:
        apm["编排控制"] = "❌ 薄弱 — 多步骤协调混乱，大幅冗余消耗资源"

    # 安全控制 (Security Control) — 关联合规性、可控性和准确性
    sec_avg = (scores.get("compliance", 0) + scores.get("controllability", 0) + scores.get("accuracy", 0)) / 3
    if sec_avg >= 80:
        apm["安全控制"] = "✅ 良好 — 全链路安全护栏覆盖，对抗鲁棒性强，审计完整"
    elif sec_avg >= 60:
        apm["安全控制"] = "⚠️ 需改进 — 部分环节缺少安全防护或审计覆盖不足"
    else:
        apm["安全控制"] = "❌ 薄弱 — 安全机制严重缺失，存在合规和对抗风险"

    # 全流程可观测性 — 关联响应速度和稳定性
    obs_avg = (scores.get("speed", 0) + scores.get("stability", 0)) / 2
    if obs_avg >= 80:
        apm["全流程可观测性"] = "✅ 良好 — 全流程可追踪，各环节耗时和资源消耗可见"
    elif obs_avg >= 60:
        apm["全流程可观测性"] = "⚠️ 需改进 — 部分环节存在监控盲区"
    else:
        apm["全流程可观测性"] = "❌ 薄弱 — 执行过程几乎不透明"

    return apm


def evaluate(scores: Dict[str, float], weights: Dict[str, float]) -> Dict:
    """执行完整评估"""

    # 验证输入
    for key in DEFAULT_WEIGHTS:
        if key not in scores:
            raise ValueError(f"缺少评分维度: {key}")
        if not (0 <= scores[key] <= 100):
            raise ValueError(f"评分需在0-100之间: {key}={scores[key]}")

    weight_sum = sum(weights.get(k, 0) for k in DEFAULT_WEIGHTS)
    if abs(weight_sum - 1.0) > 0.01:
        # 归一化
        weights = {k: v / weight_sum for k, v in weights.items()}

    # 计算加权总分
    total_score = sum(scores[k] * weights.get(k, 0) for k in DEFAULT_WEIGHTS)
    total_score = round(total_score, 1)

    # 各维度详情
    dimensions = []
    for dim_key in DEFAULT_WEIGHTS:
        dim_meta = DIMENSION_META[dim_key]
        score = scores[dim_key]
        weight = weights.get(dim_key, 0)
        weighted_score = round(score * weight * 100) / 100
        dimensions.append({
            "key": dim_key,
            "name": dim_meta["name"],
            "dimension_group": dim_meta["dimension"],
            "score": score,
            "weight": round(weight * 100, 1),
            "weighted_score": weighted_score,
            "grade": get_dimension_grade(score),
            "description": dim_meta["description"]
        })

    grade, grade_desc = get_grade(total_score)
    suggestions = get_improvement_suggestions(scores, weights)
    apm = get_apm_assessment(scores)

    return {
        "total_score": total_score,
        "grade": grade,
        "grade_description": grade_desc,
        "weights_used": {k: round(v * 100, 1) for k, v in weights.items()},
        "dimensions": dimensions,
        "improvement_suggestions": suggestions,
        "apm_assessment": apm
    }


def format_report(result: Dict) -> str:
    """格式化评估报告（彩色终端输出）"""
    # ANSI 颜色
    C = {
        "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
        "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
        "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
        "white": "\033[37m",
        "bg_green": "\033[42m", "bg_red": "\033[41m", "bg_yellow": "\033[43m",
        "bg_blue": "\033[44m",
    }
    grade_color = {"A": "green", "B": "blue", "C": "yellow", "D": "yellow", "E": "red"}

    lines = []
    # 标题
    lines.append(f"{C['bold']}{C['cyan']}╔{'═'*58}╗{C['reset']}")
    lines.append(f"{C['bold']}{C['cyan']}║{C['reset']}  {C['bold']}Agent 质量评估报告 (OPI Framework){C['reset']}" + " " * 24 + f"{C['bold']}{C['cyan']}║{C['reset']}")
    lines.append(f"{C['bold']}{C['cyan']}╚{'═'*58}╝{C['reset']}")
    lines.append("")

    # 总分卡片
    gc = grade_color.get(result["grade"], "white")
    lines.append(f"  {C['bold']}总分: {C[gc]}{result['total_score']:.1f}{C['reset']} / 100  "
                 f"  {C['bold']}等级: {C[gc]}{result['grade']}{C['reset']}  "
                 f"  {C['dim']}成熟度: L{get_maturity_for_report(result['total_score'])}{C['reset']}")
    lines.append(f"  {C['dim']}{result['grade_description']}{C['reset']}")
    lines.append("")

    # 六维得分表格
    lines.append(f"  {C['bold']}┌──────────────────────┬──────┬──────┬──────┬──────────┐{C['reset']}")
    lines.append(f"  {C['bold']}│ 评估轴                │ 得分  │ 权重  │ 加权  │ 损失分    │{C['reset']}")
    lines.append(f"  {C['bold']}├──────────────────────┼──────┼──────┼──────┼──────────┤{C['reset']}")
    for d in result["dimensions"]:
        s = d["score"]
        gc = "green" if s >= 85 else "blue" if s >= 70 else "yellow" if s >= 55 else "red"
        bar_w = s // 5
        bar_full = "█" * bar_w
        bar_empty = "░" * (20 - bar_w)
        loss = round((100 - s) * d["weight"] / 100, 1)
        lines.append(
            f"  {C['bold']}│{C['reset']} {d['name']:<20s} "
            f"{C['bold']}{C[gc]}{d['score']:>4d}{C['reset']}  "
            f"{d['weight']:>4.0f}%  "
            f"{d['weighted_score']:>5.1f}  "
            f"{C['yellow'] if loss > 5 else C['dim']}{loss:>6.1f}{C['reset']}  "
            f"{C['bold']}│{C['reset']}"
        )
        lines.append(
            f"  {C['bold']}│{C['reset']} {C[gc]}{bar_full}{C['dim']}{bar_empty}{C['reset']}       "
            f"{C['dim']}{get_grade_short(d['grade'])}{C['reset']}            {C['bold']}│{C['reset']}"
        )
    lines.append(f"  {C['bold']}└──────────────────────┴──────┴──────┴──────┴──────────┘{C['reset']}")
    lines.append("")

    # 改进建议
    lines.append(f"  {C['bold']}改进建议（按加权损失分排序）{C['reset']}")
    lines.append(f"  {C['dim']}{'─'*46}{C['reset']}")
    for i, sug in enumerate(result["improvement_suggestions"][:3], 1):
        p_color = "red" if "高" in sug.get("priority", "") else "yellow" if "中" in sug.get("priority", "") else "blue"
        lines.append(
            f"  {C['bold']}{C[p_color]}P{i-1}{C['reset']} {sug['name']} "
            f"{C['dim']}({sug['score']:.0f}分 · 损失{sug['weighted_loss']:.1f}){C['reset']}"
        )
        for s in sug.get("suggestions", [])[:1]:
            lines.append(f"     {C['dim']}→ {s}{C['reset']}")
    lines.append("")

    # APM 摘要
    lines.append(f"  {C['bold']}APM 管控点{C['reset']}")
    apm_statuses = result.get("apm_assessment", {})
    apm_ok = sum(1 for v in apm_statuses.values() if "✅" in v)
    apm_warn = sum(1 for v in apm_statuses.values() if "⚠️" in v)
    apm_fail = sum(1 for v in apm_statuses.values() if "❌" in v)
    lines.append(
        f"  {C['green']}✅ {apm_ok} 达标{C['reset']}  "
        f"{C['yellow']}⚠️ {apm_warn} 部分{C['reset']}  "
        f"{C['red']}❌ {apm_fail} 未达标{C['reset']}"
    )

    lines.append("")
    lines.append(f"{C['bold']}{C['cyan']}{'═'*60}{C['reset']}")
    return "\n".join(lines)


def get_maturity_for_report(score: float) -> str:
    """从分数推导成熟度等级"""
    if score >= 85: return "5"
    if score >= 70: return "4"
    if score >= 55: return "3"
    if score >= 40: return "2"
    return "1"


def get_grade_short(grade_str: str) -> str:
    grades = {"优秀": "优", "良好": "良", "及格": "及", "较差": "差", "不合格": "劣"}
    return grades.get(grade_str, grade_str)


def load_config(config_path: str) -> Dict:
    """从JSON配置文件加载评估参数"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent 质量评估工具 (OPI Framework)"
    )
    parser.add_argument("--config", help="JSON配置文件路径")
    parser.add_argument("--scores", help='评分JSON，如 {"accuracy":85,"stability":70,...}')
    parser.add_argument("--weights", help='权重JSON（可选，默认使用通用场景权重）')
    parser.add_argument("--preset", 
                        choices=["通用场景", "受监管行业（金融/法律/医疗）", "实时服务（ChatBot/在线客服）"],
                        default="通用场景",
                        help="权重预设")
    parser.add_argument("--output", "-o", help="输出报告到文件")
    parser.add_argument("--json-output", action="store_true", 
                        help="输出JSON格式（用于程序化处理）")

    args = parser.parse_args()

    # 加载配置
    if args.config:
        config = load_config(args.config)
        scores = config["scores"]
        weights = config.get("weights", None)
    elif args.scores:
        scores = json.loads(args.scores)
        weights = json.loads(args.weights) if args.weights else None
    else:
        # 交互模式
        print("Agent 质量评估工具 (OPI Framework)")
        print("=" * 40)
        scores = {}
        dim_info = [
            ("accuracy", "准确性", "输出内容是否准确可信，有引用来源"),
            ("stability", "稳定性", "持续运行、异常输入下的一致行为"),
            ("speed", "响应速度", "全链路等待时间与进度可感知性"),
            ("controllability", "可控性", "行为范围与边界干预机制"),
            ("cost", "成本", "Token消耗与工具调用的业务可控性"),
            ("compliance", "合规性", "输出是否满足行业合规要求"),
        ]
        for key, name, desc in dim_info:
            while True:
                try:
                    val = float(input(f"\n{name} ({desc})\n请输入评分 (0-100): "))
                    if 0 <= val <= 100:
                        scores[key] = val
                        break
                    print("评分需在 0-100 之间")
                except ValueError:
                    print("请输入有效数字")

        print("\n选择权重预设:")
        for name in WEIGHT_PRESETS:
            print(f"  - {name}")
        preset_choice = input("预设名称（直接回车使用默认）: ").strip()
        if preset_choice in WEIGHT_PRESETS:
            weights = WEIGHT_PRESETS[preset_choice]
        else:
            weights = DEFAULT_WEIGHTS

    if weights is None:
        weights = WEIGHT_PRESETS.get(args.preset, DEFAULT_WEIGHTS)

    # 执行评估
    result = evaluate(scores, weights)

    # 输出
    if args.json_output:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_report(result)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"报告已保存至: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
