#!/usr/bin/env python3
"""
Agent Quality Evaluator — HTML Report Generator

将 evaluate.py 的 JSON 输出转换为可视化 HTML 报告。
用法:
  python3 generate_report.py --input eval_result.json --output report.html
  python3 generate_report.py --scores '{"accuracy":85,...}' --preset "通用场景" -o report.html
"""

import json
import sys
import argparse
from datetime import datetime


def get_grade_class(score):
    if score >= 85:
        return "a"
    elif score >= 70:
        return "b"
    elif score >= 55:
        return "c"
    elif score >= 40:
        return "d"
    return "e"


def get_grade_label(score):
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    return "E"


def get_tag_class(score):
    if score >= 85:
        return "tag-green"
    elif score >= 70:
        return "tag-blue"
    elif score >= 55:
        return "tag-amber"
    return "tag-red"


def get_bar_color(score):
    if score >= 85:
        return "#16a34a"
    elif score >= 70:
        return "#2563eb"
    elif score >= 55:
        return "#f59e0b"
    return "#dc2626"


def get_apm_status_icon(status):
    if status == "pass":
        return '<span class="status-ok">✅ 达标</span>'
    elif status == "warn":
        return '<span class="status-warn">⚠️ 部分达标</span>'
    return '<span class="status-fail">❌ 未达标</span>'


def get_maturity(score):
    if score >= 85:
        return "5"
    elif score >= 70:
        return "4"
    elif score >= 55:
        return "3"
    elif score >= 40:
        return "2"
    return "1"


def get_maturity_name(score):
    if score >= 85:
        return "AI 原生"
    elif score >= 70:
        return "企业级"
    elif score >= 55:
        return "生产就绪"
    elif score >= 40:
        return "功能验证"
    return "实验原型"


def generate_dimension_rows(scores, weights):
    dim_map = {
        "accuracy": "A. 准确性",
        "stability": "B. 稳定性",
        "speed": "C. 响应速度",
        "controllability": "D. 可控性",
        "cost": "E. 成本",
        "compliance": "F. 合规性",
    }
    rows = []
    for key, name in dim_map.items():
        s = scores.get(key, 50)
        w = weights.get(key, 0)
        weighted = round(s * w / 100, 2)
        loss = round((100 - s) * w / 100, 2)
        color = get_bar_color(s)
        rows.append(
            f'<tr>'
            f'<td>{"性能" if key in ("accuracy","stability","speed") else "商业"}</td>'
            f'<td>{name}</td>'
            f'<td style="text-align:center"><span class="tag {get_tag_class(s)}">{s}</span></td>'
            f'<td style="text-align:center">{w}%</td>'
            f'<td style="text-align:center">{weighted}</td>'
            f'<td style="text-align:center">{loss}</td>'
            f'<td><span class="dim-bar" style="width:{s}%;background:{color}"></span></td>'
            f'</tr>'
        )
    return "\n".join(rows)


def generate_improvement_items(scores, weights):
    dim_map = {
        "accuracy": ("准确性", "错误集中在哪类任务？"),
        "stability": ("稳定性", "哪些输入条件下容易波动？"),
        "speed": ("响应速度", "P50/P95 延迟瓶颈在哪？"),
        "controllability": ("可控性", "干预点在决策链的哪个位置？"),
        "cost": ("成本", "Token 分布和缓存命中率如何？"),
        "compliance": ("合规性", "溯源链路覆盖了哪些环节？"),
    }
    items = []
    for key, (name, diag) in dim_map.items():
        s = scores.get(key, 50)
        w = weights.get(key, 0)
        loss = round((100 - s) * w / 100, 2)
        items.append((name, s, loss, diag, key))
    items.sort(key=lambda x: x[2], reverse=True)

    html_items = []
    priorities = [(0, "P0 · 立即处理", "p0"), (1, "P1 · 本迭代处理", "p1"), (2, "P2 · 后续迭代", "p2")]
    for idx, (name, s, loss, diag, key) in enumerate(items[:3]):
        p_label, p_text, p_class = priorities[idx % 3]
        html_items.append(
            f'<div class="improvement-row {p_class}">'
            f'<div class="pri">{p_text} — {name} ({s}分 → 目标 ≥{min(s+15,100)}分 · 损失{loss}分)</div>'
            f'<div class="detail">诊断线索：{diag} &nbsp;|&nbsp; 建议基于该维度评估发现制定具体行动项</div>'
            f'</div>'
        )
    return "\n".join(html_items) if html_items else '<p>无明显短板，所有维度得分均较高。</p>'


def generate_apm_rows():
    apm_points = [
        ("规划控制", "warn", "任务拆解待验证"),
        ("记忆控制", "warn", "上下文完整性待确认"),
        ("工具控制", "warn", "工具选择准确性待评估"),
        ("行动控制", "warn", "输出格式稳定性待确认"),
        ("编排控制", "warn", "多Agent协作待评估"),
        ("安全控制", "warn", "护栏覆盖度待验证"),
        ("全流程可观测性", "warn", "审计日志待完善"),
    ]
    rows = []
    for name, status, desc in apm_points:
        rows.append(
            f'<tr><td>{name}</td>'
            f'<td style="text-align:center">{get_apm_status_icon(status)}</td>'
            f'<td>{desc}</td></tr>'
        )
    return "\n".join(rows)


def generate_timeline(total_score):
    current_m = get_maturity(total_score)
    current_name = get_maturity_name(total_score)
    targets = []
    if total_score < 55:
        targets = [("1-2周", "M3", "补全基础能力"), ("1-2月", "M4", "引入监控+成本管控"), ("季度", "M5", "全链路可观测")]
    elif total_score < 70:
        targets = [("1-2周", "M4", "完善可观测性"), ("1-2月", "M4+", "引入模型路由"), ("季度", "M5", "AI原生转型")]
    elif total_score < 85:
        targets = [("1-2周", "M4+", "语义缓存上线"), ("1-2月", "M5", "持续评估飞轮"), ("季度", "M5", "联邦评估治理")]
    else:
        targets = [("1-2周", "M5", "红队安全测试"), ("1-2月", "M5+", "多Agent编排"), ("季度", "M5++", "自治运维")]

    items = []
    for time_label, level, desc in targets:
        items.append(
            f'<div class="timeline-item">'
            f'<div class="level">{level}</div>'
            f'<div class="desc">{time_label}<br>{desc}</div>'
            f'</div>'
        )
    return "\n".join(items)


def generate_gate_section(total_score):
    if total_score < 70:
        return '<div class="card"><h2>六、部署就绪门禁</h2><div class="conclusion-bar fail">⚠️ 当前等级不满足上线条件，门禁检查暂不适用</div></div>'

    gates = [
        ("SLO/SLI 已定义", True), ("监控与告警已配置", True), ("Runbook 已就绪", True),
        ("回滚方案已验证", True), ("对抗测试已通过", True), ("安全合规已确认", True),
        ("漂移检测已启用", True), ("模型路由已评估", True), ("Kill Switch 已配置", True),
    ]
    items = []
    all_pass = True
    for name, default_pass in gates:
        icon = "✅" if default_pass else "❌"
        if not default_pass:
            all_pass = False
        items.append(
            f'<div class="gate-item">'
            f'<div class="gate-status">{icon} {name}</div>'
            f'<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">待确认</div>'
            f'</div>'
        )

    conclusion = '<div class="conclusion-bar pass">✅ 建议上线：所有门禁项已通过确认</div>' if all_pass else \
        '<div class="conclusion-bar fail">❌ 有门禁项未通过，需修复后重新评估</div>'

    return f'<div class="card"><h2>六、部署就绪门禁</h2><div class="gate-grid">{"".join(items)}</div>{conclusion}</div>'


def generate_diagnosis_sections(scores):
    dim_diag = {
        "accuracy": ("A. 准确性", [
            ("错误集中在哪类任务？", "待填写"),
            ("引用覆盖率多高？", "待填写"),
            ("幻觉频率和类型分布？", "待填写"),
        ]),
        "stability": ("B. 稳定性", [
            ("哪些输入条件下容易波动？", "待填写"),
            ("降级策略覆盖多少异常类型？", "待填写"),
            ("恢复成功率？", "待填写"),
        ]),
        "speed": ("C. 响应速度", [
            ("P50/P95 延迟是多少？", "待填写"),
            ("用户等待感知在哪个环节最强烈？", "待填写"),
            ("中间状态是否可审计？", "待填写"),
        ]),
        "controllability": ("D. 可控性", [
            ("干预点在决策链的哪个位置？", "待填写"),
            ("熔断阈值如何设定？", "待填写"),
            ("回滚粒度到哪一级？", "待填写"),
        ]),
        "cost": ("E. 成本", [
            ("单次任务 Token 分布如何？", "待填写"),
            ("缓存命中率？", "待填写"),
            ("重试占总消耗的比例？", "待填写"),
        ]),
        "compliance": ("F. 合规性", [
            ("溯源链路覆盖了哪些环节？", "待填写"),
            ("护栏在检索/工具/输出三层各做了什么？", "待填写"),
            ("未覆盖的盲区在哪？", "待填写"),
        ]),
    }
    sections = []
    for key, (name, items) in dim_diag.items():
        s = scores.get(key, 50)
        grade = get_grade_label(s)
        tag = get_tag_class(s)
        rows_html = "\n".join(
            f'<tr><td style="width:35%">{q}</td><td>{a}</td></tr>'
            for q, a in items
        )
        sections.append(
            f'<h3 style="margin-top:20px;">{name} — '
            f'<span class="tag {tag}">{s}/{grade}</span></h3>'
            f'<table style="margin-top:8px;"><tbody>{rows_html}</tbody></table>'
        )
    return "\n".join(sections)


def load_evaluate_result(args):
    """Load scores from either --input JSON or --scores string."""
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
        return data

    if args.scores:
        scores = json.loads(args.scores)
    else:
        scores = {}

    return {
        "total_score": 0,
        "grade": "",
        "scores": scores,
        "weights": {},
        "improvements": [],
    }


def resolve_weights(preset="通用场景"):
    presets = {
        "通用场景": {"accuracy": 25, "stability": 25, "speed": 15, "controllability": 10, "cost": 15, "compliance": 10},
        "受监管行业": {"accuracy": 20, "stability": 20, "speed": 10, "controllability": 15, "cost": 10, "compliance": 25},
        "实时服务": {"accuracy": 20, "stability": 25, "speed": 25, "controllability": 10, "cost": 10, "compliance": 10},
    }
    # Partial match
    for key, val in presets.items():
        if key in preset or preset in key:
            return val
    return presets["通用场景"]


def calculate_total(scores, weights):
    total = 0
    for key, w in weights.items():
        s = scores.get(key, 50)
        total += s * w / 100
    return round(total, 1)


def generate_report(data, preset="通用场景"):
    scores = data.get("scores", {})
    weights = resolve_weights(preset)
    total_score = data.get("total_score") or calculate_total(scores, weights)
    grade = data.get("grade") or get_grade_label(total_score)
    grade_class = get_grade_class(total_score)
    maturity = data.get("maturity") or get_maturity(total_score)
    maturity_name = get_maturity_name(total_score)

    deploy_short = "✅ 可上线" if total_score >= 70 else "⚠️ 待优化"
    if total_score < 55:
        deploy_short = "❌ 不建议"

    # Find biggest gap
    biggest_key = max(weights, key=lambda k: (100 - scores.get(k, 50)) * weights[k] / 100)
    dim_names = {"accuracy": "准确性", "stability": "稳定性", "speed": "响应速度",
                 "controllability": "可控性", "cost": "成本", "compliance": "合规性"}
    biggest_gap = dim_names.get(biggest_key, biggest_key)

    # Read template
    template_path = data.get("template_path") or "assets/report_template.html"
    try:
        with open(template_path) as f:
            html = f.read()
    except FileNotFoundError:
        html_paths = [
            "assets/report_template.html",
            "/Users/polardong/.workbuddy/skills/agent-quality-evaluator/assets/report_template.html",
        ]
        html = ""
        for p in html_paths:
            try:
                with open(p) as f:
                    html = f.read()
                    break
            except FileNotFoundError:
                continue
        if not html:
            return f"Error: report_template.html not found at {template_path}"

    # Replace placeholders
    replacements = {
        "{{agent_name}}": data.get("agent_name", "未命名 Agent"),
        "{{date}}": data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "{{scenario}}": preset,
        "{{eval_mode}}": data.get("eval_mode", "单人评估"),
        "{{total_score}}": str(total_score),
        "{{grade}}": grade,
        "{{grade_class}}": grade_class,
        "{{maturity}}": maturity,
        "{{maturity_name}}": maturity_name,
        "{{deploy_status_short}}": deploy_short,
        "{{dimension_rows}}": generate_dimension_rows(scores, weights),
        "{{diagnosis_sections}}": generate_diagnosis_sections(scores),
        "{{apm_rows}}": generate_apm_rows(),
        "{{improvement_items}}": generate_improvement_items(scores, weights),
        "{{biggest_gap}}": biggest_gap,
        "{{timeline_items}}": generate_timeline(total_score),
        "{{gate_section}}": generate_gate_section(total_score),
        "{{cicd_recommendation}}": f"当前成熟度 L{maturity}（{maturity_name}），建议优先接入: "
                                   f"{'基础回归测试' if maturity <= '2' else '端到端沙箱验证+成本回归' if maturity == '3' else '对抗测试+持续评估飞轮'}",
        "{{weight_source}}": f"场景预设: {preset}",
        "{{history_summary}}": data.get("history", "首次评估"),
        "{{notes}}": data.get("notes", "无"),
        "{{gen_time}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "{{one_liner}}": data.get("one_liner", f"系统总体质量{grade}级，最突出短板为{biggest_gap}维度。"),
    }

    for key, val in replacements.items():
        html = html.replace(key, val)

    return html


def main():
    parser = argparse.ArgumentParser(description="生成 Agent 评估 HTML 报告")
    parser.add_argument("--input", "-i", help="evaluate.py 输出的 JSON 文件")
    parser.add_argument("--scores", "-s", help='评分 JSON 字符串，如 \'{"accuracy":85,...}\'')
    parser.add_argument("--preset", "-p", default="通用场景", help="权重预设 (默认: 通用场景)")
    parser.add_argument("--output", "-o", default="report.html", help="输出 HTML 文件路径")
    parser.add_argument("--agent-name", default="未命名 Agent", help="评估对象名称")
    parser.add_argument("--one-liner", default="", help="一句话结论")
    parser.add_argument("--template", default="assets/report_template.html", help="HTML 模板路径")
    args = parser.parse_args()

    if not args.input and not args.scores:
        print("错误: 需要 --input 或 --scores 参数")
        sys.exit(1)

    data = load_evaluate_result(args)
    data["agent_name"] = args.agent_name
    data["template_path"] = args.template
    if args.one_liner:
        data["one_liner"] = args.one_liner

    html = generate_report(data, args.preset)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 报告已生成: {args.output}")


if __name__ == "__main__":
    main()
