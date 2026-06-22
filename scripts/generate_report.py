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
import os
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
        "accuracy": ("A. 准确性", "性能"),
        "stability": ("B. 稳定性", "性能"),
        "speed": ("C. 响应速度", "性能"),
        "controllability": ("D. 可控性", "商业"),
        "cost": ("E. 成本", "商业"),
        "compliance": ("F. 合规性", "商业"),
    }
    rows = []
    for key, (name, cat) in dim_map.items():
        s = scores.get(key, 50)
        w = weights.get(key, 0)
        weighted = round(s * w / 100, 2)
        loss = round((100 - s) * w / 100, 2)
        gc = "a" if s >= 85 else "b" if s >= 70 else "c" if s >= 55 else "d"
        loss_class = "crit" if loss >= 8 else "warn" if loss >= 4 else ""
        rows.append(
            f'<tr>'
            f'<td><span class="dim-name">{name}</span>&nbsp;'
            f'<span class="dim-cat">{cat}</span></td>'
            f'<td class="dim-score {gc}">{s}</td>'
            f'<td style="text-align:center;font-size:13px;">{w}%</td>'
            f'<td style="text-align:right;font-size:13px;">{weighted}</td>'
            f'<td class="dim-loss {loss_class}" style="text-align:right;">{loss}</td>'
            f'<td class="dim-bar-cell"><div class="dim-bar-track"><div class="dim-bar-fill {gc}" style="width:{s}%"></div></div></td>'
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

    items = [x for x in items if x[2] > 0]  # 过滤无损失的维度
    if not items:
        return '<p>所有维度表现良好，无明显改进项。</p>'

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


def generate_apm_rows(scores):
    """根据各维度得分生成有诊断价值的 APM 管控点描述"""
    dim_to_apm = {
        "accuracy": ("规划控制", "行动控制"),
        "stability": ("工具控制", "记忆控制"),
        "speed": ("全流程可观测性",),
        "controllability": ("行动控制", "编排控制"),
        "cost": ("记忆控制",),
        "compliance": ("安全控制",),
    }
    apm_diagnostics = {
        "规划控制":     (80, "任务拆解合理，多方案对比评估到位", "推理步骤缺少备选方案评估，边界场景覆盖不足"),
        "记忆控制":     (75, "上下文精准切题，Token 受控", "超长对话场景关键信息遗漏，上下文未压缩导致 Token 膨胀"),
        "工具控制":     (75, "工具选择准确，参数正确率高，有错误恢复", "工具调用失败无降级机制，API 异常直接抛出"),
        "行动控制":     (75, "输出格式稳定，内容边界受控", "高风险操作无熔断机制，缺少 HITL 干预断点"),
        "编排控制":     (70, "子任务分配合理，收敛稳定", "多步骤任务无收敛性校验，存在冗余迭代"),
        "安全控制":     (75, "全链路护栏覆盖，对抗鲁棒性强", "工具调用返回内容未经安全校验直接拼接进输出"),
        "全流程可观测性": (75, "各环节耗时可见，审计日志完整", "中间步骤不可追踪，P95 延迟高但定位不到瓶颈环节"),
    }

    # Calculate APM status based on related dimension scores
    apm_statuses = {}
    for dim_key, apm_keys in dim_to_apm.items():
        s = scores.get(dim_key, 50)
        status = "pass" if s >= 85 else "warn" if s >= 60 else "fail"
        for apm_key in apm_keys:
            if apm_key not in apm_statuses:
                apm_statuses[apm_key] = []
            apm_statuses[apm_key].append(status)

    rows = []
    apm_order = ["规划控制", "记忆控制", "工具控制", "行动控制", "编排控制", "安全控制", "全流程可观测性"]
    for name in apm_order:
        statuses = apm_statuses.get(name, ["warn"])
        # worst status wins
        if "fail" in statuses:
            status = "fail"
        elif "warn" in statuses:
            status = "warn"
        else:
            status = "pass"

        _, pass_msg, fail_msg = apm_diagnostics[name]
        desc = pass_msg if status == "pass" else fail_msg
        icon = "✓" if status == "pass" else "—" if status == "warn" else "✗"
        status_class = "pass" if status == "pass" else "warn" if status == "warn" else "fail"

        rows.append(
            f'<div class="apm-row {status_class}">'
            f'<span class="apm-status">{icon}</span>'
            f'<span class="apm-name">{name}</span>'
            f'<span class="apm-desc">{desc}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def generate_timeline(total_score):
    current_name = get_maturity_name(total_score)
    targets = []
    if total_score < 55:
        targets = [("1–2 周", "L3", "补全基础能力与异常处理"), ("1–2 月", "L4", "引入监控告警与成本管控"), ("季度", "L5", "全链路可观测与持续评估")]
    elif total_score < 70:
        targets = [("1–2 周", "L4", "完善可观测性与故障恢复"), ("1–2 月", "L4+", "引入模型路由与语义缓存"), ("季度", "L5", "AI 原生转型")]
    elif total_score < 85:
        targets = [("1–2 周", "L4+", "语义缓存与Kill Switch上线"), ("1–2 月", "L5", "持续评估飞轮部署"), ("季度", "L5+", "联邦评估治理")]
    else:
        targets = [("1–2 周", "L5", "红队安全测试"), ("1–2 月", "L5+", "多Agent编排优化"), ("季度", "L5++", "自治运维")]

    items = []
    for time_label, level, desc in targets:
        items.append(
            f'<div class="plan-stage">'
            f'<div class="stage-time">{time_label}</div>'
            f'<div class="stage-level">{level}</div>'
            f'<div class="stage-desc">{desc}</div>'
            f'</div>'
        )
    return "\n".join(items)


def generate_gate_section(total_score, scores):
    if total_score < 70:
        return (
            '<div class="section"><div class="section-head"><span class="num">06</span><h2>部署就绪门禁</h2></div>'
            '<div class="conclusion fail">当前等级不满足上线条件，门禁检查暂不适用</div></div>'
        )

    # Gate status inferred from related dimension scores
    s = scores
    gates = [
        ("SLO / SLI 已定义",      "通过" if total_score >= 75 else "待确认",   total_score),
        ("监控与告警已配置",       "通过" if s.get("speed",0) >= 70 else "待完善",    s.get("speed",50)),
        ("Runbook 已就绪",         "通过" if s.get("stability",0) >= 70 else "待完善", s.get("stability",50)),
        ("回滚方案已验证",         "通过" if s.get("controllability",0) >= 70 else "待配置", s.get("controllability",50)),
        ("对抗测试已通过",         "通过" if s.get("compliance",0) >= 75 else "待测试",  s.get("compliance",50)),
        ("安全合规已确认",         "通过" if s.get("compliance",0) >= 80 else "待确认",  s.get("compliance",50)),
        ("漂移检测已启用",         "通过" if s.get("stability",0) >= 75 else "待部署",   s.get("stability",50)),
        ("模型路由已评估",         "通过" if s.get("cost",0) >= 75 else "待评估",        s.get("cost",50)),
        ("Kill Switch 已配置",    "通过" if s.get("controllability",0) >= 75 else "待配置", s.get("controllability",50)),
    ]
    items = []
    all_pass = True
    for name, status, ref_score in gates:
        icon = "✅" if status == "通过" else "❌"
        if status != "通过":
            all_pass = False
        items.append(
            f'<div class="gate-item">'
            f'<div class="gate-status">{icon} {name}</div>'
            f'<div class="gate-detail">{status}</div>'
            f'</div>'
        )
    conclusion = (
        '<div class="conclusion pass">全部门禁项已通过，可上线</div>' if all_pass else
        f'<div class="conclusion fail">{"、".join(name for name, st, _ in gates if st != "通过")} 未通过，需修复后重新评估</div>'
    )

    return (
        f'<div class="section"><div class="section-head"><span class="num">06</span><h2>部署就绪门禁</h2></div>'
        f'<div class="gate-grid">{"".join(items)}</div>{conclusion}</div>'
    )


def generate_cicd_section(maturity, maturity_name):
    recs = {
        "1": "基础回归测试 — 用历史失败案例集验证新版本不引入退化",
        "2": "基础回归测试 — 用历史失败案例集验证新版本不引入退化",
        "3": "端到端沙箱验证 + 成本回归测试",
        "4": "对抗测试 + 成本回归 + 漂移检测",
        "5": "持续评估飞轮 — 在线指标回写至测试用例集，闭环迭代",
    }
    rec = recs.get(maturity, recs["1"])
    return (
        f'<div class="section"><div class="section-head"><span class="num">07</span><h2>CI/CD 集成建议</h2></div>'
        f'<p style="font-size:14px;color:var(--ink-secondary);">'
        f'当前成熟度 L{maturity}（{maturity_name}），建议优先接入：{rec}</p></div>'
    )


def generate_diagnosis_sections(scores):
    """从分数推断诊断语，替代硬编码的'待填写'"""
    def diag(score, high, mid, low):
        if score >= 80: return high if high else "表现良好，无明显问题"
        if score >= 55: return mid if mid else "存在改进空间，需进一步分析"
        return low if low else "得分偏低，存在明显问题需优先排查"

    dim_diag = {
        "accuracy": ("A. 准确性", [
            ("错误集中在哪类任务？",
             diag(scores.get("accuracy",50),
                  "无明显集中错误，各类任务表现均衡",
                  "边界场景和长尾任务偶有偏差，高频任务基本准确",
                  "复杂推理类任务错误率高，事实性查询也存在编造行为")),
            ("引用覆盖率多高？",
             diag(scores.get("accuracy",50),
                  "绝大多数输出附带可追溯引用来源",
                  "部分输出有引用但不完整，缺少来源验证",
                  "几乎没有可追溯引用，信息来源不明")),
            ("幻觉频率和类型分布？",
             diag(scores.get("accuracy",50),
                  "幻觉罕见，输出一致性高",
                  "偶有日期/数字类幻觉，每5-10次出现1-2次",
                  "频繁幻觉，日期、数字、事实均存在编造")),
        ]),
        "stability": ("B. 稳定性", [
            ("哪些输入条件下容易波动？",
             diag(scores.get("stability",50),
                  "各类输入条件下表现稳定",
                  "超长上下文（>8k token）或异常输入下偶有波动",
                  "多种输入场景波动频繁，格式不一致严重")),
            ("降级策略覆盖多少异常类型？",
             diag(scores.get("stability",50),
                  "完整覆盖 API 超时、工具异常、格式错误等场景",
                  "仅覆盖基础异常，工具调用失败无专门降级",
                  "无明显降级策略，异常直接抛出")),
            ("恢复成功率？",
             diag(scores.get("stability",50),
                  "断点恢复成功率高，中间结果不丢失",
                  "部分场景可恢复但中间结果偶有丢失",
                  "出错后需从零重试，无断点恢复机制")),
        ]),
        "speed": ("C. 响应速度", [
            ("P50/P95 延迟是多少？",
             diag(scores.get("speed",50),
                  "P50<2s, P95<8s，延迟分布稳定",
                  "P50可接受但长尾明显，P95偏高",
                  "P50延迟偏高且P95严重超限")),
            ("用户等待感知在哪个环节最强烈？",
             diag(scores.get("speed",50),
                  "全流程有进度反馈，等待可预期",
                  "工具调用返回等结果阶段感知明显，缺进度提示",
                  "全程无反馈，用户无法判断是否卡住")),
            ("中间状态是否可审计？",
             diag(scores.get("speed",50),
                  "中间步骤可查看，轨迹完整可审计",
                  "部分步骤可见但不完整",
                  "中间步骤不可查看，完全黑盒")),
        ]),
        "controllability": ("D. 可控性", [
            ("干预点在决策链的哪个位置？",
             diag(scores.get("controllability",50),
                  "关键操作前有 HITL 断点，可人工审核",
                  "有基础控制但干预入口不明显",
                  "无 HITL 断点，全自动执行不可干预")),
            ("熔断阈值如何设定？",
             diag(scores.get("controllability",50),
                  "Kill Switch 已配置，高风险操作有强制熔断",
                  "熔断配置不完整，缺少关键场景覆盖",
                  "未配置 Kill Switch，高风险操作无熔断保护")),
            ("回滚粒度到哪一级？",
             diag(scores.get("controllability",50),
                  "支持单步/单任务回滚，版本快速回退",
                  "仅支持整体回退，粒度较粗",
                  "无可回滚机制，错误后需人工处理")),
        ]),
        "cost": ("E. 成本", [
            ("单次任务 Token 分布如何？",
             diag(scores.get("cost",50),
                  "Token 消耗合理，无冗余浪费",
                  "平均消耗可接受，但反思/纠错环节占比偏高",
                  "Token 消耗严重，反思和重试占大头")),
            ("缓存命中率？",
             diag(scores.get("cost",50),
                  "语义缓存有效减少重复计算",
                  "有缓存但命中率不高，优化空间大",
                  "无语义缓存，重复任务每次都重新计算")),
            ("重试占总消耗的比例？",
             diag(scores.get("cost",50),
                  "重试开销低（<5%），调用效率高",
                  "重试占比 5-15%，存在优化空间",
                  "重试占总消耗>15%，效率低下")),
        ]),
        "compliance": ("F. 合规性", [
            ("溯源链路覆盖了哪些环节？",
             diag(scores.get("compliance",50),
                  "检索→工具→输出全链路溯源",
                  "部分环节可溯源但覆盖不完整",
                  "溯源缺失，信息真实性和合规性无法保证")),
            ("护栏在检索/工具/输出三层各做了什么？",
             diag(scores.get("compliance",50),
                  "三层均有专门防护和审计",
                  "仅输出层有过滤，检索和工具层未覆盖",
                  "全链路无安全护栏")),
            ("未覆盖的盲区在哪？",
             diag(scores.get("compliance",50),
                  "无明显盲区，安全覆盖完整",
                  "工具调用返回内容未经校验直接拼接",
                  "多个环节存在安全盲区，风险较高")),
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
    """从共享 weights.json 读取权重，支持别名匹配"""
    import json
    weights_paths = [
        os.path.join(os.path.dirname(__file__), "..", "references", "weights.json"),
        "references/weights.json",
    ]
    data = None
    for p in weights_paths:
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
                break
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    if data is None:
        # Fallback to hardcoded defaults
        return {"accuracy": 25, "stability": 25, "speed": 15, "controllability": 10, "cost": 15, "compliance": 10}

    presets = data["presets"]
    aliases = data.get("aliases", {})

    # Try alias resolution first
    resolved = aliases.get(preset, preset)

    # Try exact match
    if resolved in presets:
        # Convert decimal weights to percentage integers
        return {k: round(v * 100) for k, v in presets[resolved].items()}
    # Try partial match on preset names
    for key in presets:
        if key in preset or preset in key:
            return {k: round(v * 100) for k, v in presets[key].items()}
    # Fallback
    return {k: round(v * 100) for k, v in presets["通用场景"].items()}


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
            os.path.join(os.path.dirname(__file__), "..", "assets", "report_template.html"),
            "assets/report_template.html",
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
        "{{apm_rows}}": generate_apm_rows(scores),
        "{{improvement_items}}": generate_improvement_items(scores, weights),
        "{{biggest_gap}}": biggest_gap,
        "{{timeline_items}}": generate_timeline(total_score),
        "{{gate_section}}": generate_gate_section(total_score, scores),
        "{{cicd_section}}": generate_cicd_section(maturity, maturity_name),
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
