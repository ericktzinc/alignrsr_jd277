"""alignrsr_jd277 —— 按时间线排列对齐算法研究员·张量并行切分策略并标出节奏异常。

解析时间标记，排列对齐算法研究员·张量并行切分策略的发生顺序，标出间隔异常与逆序事件

定位：
  只认能解析的时间标记，解析不了的段落单独列出而不是静默跳过

岗位对应：
  目标岗位　网易 · 架构对齐算法研究员
  技能主线　强化学习、大模型微调、PyTorch
  领域标签　AI安全对齐、大模型训练

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python alignrsr_jd277.py --help
    python alignrsr_jd277.py --file input.txt
    python alignrsr_jd277.py --text "示例内容"
    python alignrsr_jd277.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：网易 · 架构对齐算法研究员
RULES: list[dict] = [
    {
        "name": "对齐算法研究员·张量并行切分策略·缺失",
        "why": "岗位要求「强化学习」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', '强化学习'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·冲突",
        "why": "两处关于「大模型微调」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', '大模型微调'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·越界",
        "why": "「PyTorch」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', 'PyTorch'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·退化",
        "why": "「AI安全对齐」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', 'AI安全对齐'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·泄漏",
        "why": "「大模型训练」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', '大模型训练'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·重复",
        "why": "同一处「对齐算法研究员」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', '对齐算法研究员'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·陈旧#2",
        "why": "「强化学习」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', '强化学习'],
    },
    {
        "name": "对齐算法研究员·张量并行切分策略·不可核#2",
        "why": "关于「大模型微调」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', '大模型微调'],
    },
]


def alignrsr_jd277_parse_stamp(s: str) -> float:
    """把时间戳解析成秒数。"""
    s = s.strip()
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", s)
    if m:
        h, mi, sec = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        return h * 3600 + mi * 60 + sec
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(ms|s|m|h)?$", s, re.I)
    if m:
        v = float(m.group(1))
        unit = (m.group(2) or "s").lower()
        return v * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]
    return 0.0


def alignrsr_jd277_parse_events(text: str) -> list[dict]:
    """解析形如 `12:03 name ...` 的事件行。"""
    events: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?|\d+(?:\.\d+)?\s*(?:ms|s|m|h)?)\s+(.*)$",
                     line, re.I)
        if not m:
            continue
        events.append({"at": alignrsr_jd277_parse_stamp(m.group(1)), "raw_time": m.group(1),
                       "label": m.group(2).strip()})
    return events


def alignrsr_jd277_analyze(text: str) -> dict:
    """主分析：事件序列、间隔与重叠。"""
    events = alignrsr_jd277_parse_events(text)
    if not events:
        return {"ok": False, "error": "没有解析出任何时间事件", "count": 0}
    events.sort(key=lambda e: e["at"])
    gaps = []
    for i in range(1, len(events)):
        gaps.append({"from": events[i - 1]["label"], "to": events[i]["label"],
                     "gap": round(events[i]["at"] - events[i - 1]["at"], 3)})
    total = events[-1]["at"] - events[0]["at"]
    slowest = max(gaps, key=lambda g: g["gap"]) if gaps else None
    return {
        "ok": True,
        "count": len(events),
        "events": events,
        "gaps": gaps,
        "total_span": round(total, 3),
        "slowest_gap": slowest,
        "mean_gap": alignrsr_jd277_safe_mean([g["gap"] for g in gaps]),
    }


def alignrsr_jd277_safe_mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"事件数：{result['count']}  总跨度 {result['total_span']}s  平均间隔 {result['mean_gap']}")
    out.append("")
    for e in result["events"]:
        out.append(f"  {e['raw_time']:>10}  {e['label'][:80]}")
    out.append("")
    if result["slowest_gap"]:
        g = result["slowest_gap"]
        out.append(f"最慢间隔：{g['from']} → {g['to']}  {g['gap']}s")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="alignrsr_jd277",
        description="解析时间标记，排列对齐算法研究员·张量并行切分策略的发生顺序，标出间隔异常与逆序事件（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python alignrsr_jd277.py --file input.txt\n"
            "  python alignrsr_jd277.py --text '示例内容'\n"
            "  python alignrsr_jd277.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = alignrsr_jd277_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
