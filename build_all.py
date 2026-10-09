#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量渲染模拟题 JSON → HTML，并生成索引页 index.html"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOCKS = ROOT / "mocks"

STYLE = """
<style>
:root{--ink:#1f5c3d;--ink2:#25654a;--paper:#fffdf8;--bg:#f6f3ec;--line:#dfe8e1;}
body{margin:0;padding:0;background:var(--bg);}
.wrap{max-width:760px;margin:0 auto;background:var(--paper);padding:30px 26px 44px;
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
  color:#2f2f2f;line-height:1.85;font-size:16px;}
h1{color:var(--ink);font-size:23px;margin:0 0 6px;line-height:1.4;}
.sub{color:#8a8a8a;font-size:13.5px;margin-bottom:18px;}
h2{color:var(--ink);font-size:18px;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line);}
h3{color:var(--ink2);font-size:16.5px;margin:22px 0 8px;}
.qbox{background:#fbf9f3;border-left:4px solid #8fb8a0;padding:12px 16px;margin:14px 0;border-radius:0 6px 6px 0;}
.ans{background:#f2f7f3;border-left:4px solid var(--ink);padding:12px 16px;margin:10px 0 22px;border-radius:0 6px 6px 0;white-space:pre-wrap;}
.tips{background:#fff8e6;border:1px solid #f0dfae;padding:12px 16px;border-radius:6px;margin:18px 0;font-size:14.5px;color:#7a6420;}
.part{text-align:center;margin:44px 0 26px;padding:14px;background:var(--ink);color:#fff;border-radius:8px;font-size:17px;letter-spacing:2px;}
strong{color:#1a4a33;}
.foot{margin-top:36px;padding-top:14px;border-top:1px dashed #ddd6c4;color:#9a9a9a;font-size:12.5px;}
.nav{margin:16px 0 0;font-size:14px;}
.nav a{color:var(--ink);text-decoration:none;border-bottom:1px dotted var(--ink);}
.grid{display:grid;gap:12px;margin-top:16px;}
.card{display:block;padding:14px 18px;background:#fbf9f3;border:1px solid var(--line);border-radius:8px;text-decoration:none;color:#2f2f2f;}
.card:hover{background:#f2f7f3;}
.card b{color:var(--ink);font-size:16px;}
.card span{float:right;color:#8a8a8a;font-size:13px;}
.card em{display:block;margin-top:6px;font-style:normal;color:#6b6b6b;font-size:13px;line-height:1.6;}
.tbl{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px;}
.tbl th,.tbl td{border:1px solid var(--line);padding:8px 10px;text-align:left;}
.tbl th{background:#f2f7f3;color:var(--ink);}
@media print{.part{background:#fff;color:#000;border:2px solid #000;}body{background:#fff;}.wrap{max-width:none;}.tips{display:none;}}
</style>
"""


def esc(text):
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t


def build_page(m):
    parts = [
        f'<h1>{m["title"]} · 云南师范大学 347 应用心理</h1>',
        f'<div class="sub">推送日期：{m["date"]}　|　4 大题　|　满分 100 分</div>',
        f'<div class="tips">📝 {m["note"]}</div>',
        '<div class="part">第 一 部 分 · 考 题</div>',
    ]
    n = 0
    for sec in m["sections"]:
        parts.append(f'<h2>{sec["title"]}</h2>')
        for it in sec["items"]:
            n += 1
            q = esc(it["q"]).replace("\n", "<br>")
            parts.append(f'<div class="qbox"><b>{n}.</b> {q}</div>')
    parts.append('<div class="part">第 二 部 分 · 参 考 答 案</div>')
    n = 0
    for sec in m["sections"]:
        parts.append(f'<h2>{sec["title"]}</h2>')
        for it in sec["items"]:
            n += 1
            a = esc(it["a"])
            parts.append(f'<h3>{n}. {esc(it["q"].splitlines()[0])}</h3><div class="ans">{a}</div>')
    parts.append('<div class="nav">← <a href="../index.html">返回模拟题总目录</a></div>')
    parts.append('<div class="foot">云师大 347 模拟题 · 按真题结构编拟 | 答案依据彭聃龄《普通心理学》、林崇德《发展心理学》、张厚粲《现代心理与教育统计学》、戴海琦《心理与教育测量》、陈琦刘儒德《教育心理学》</div>')
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{m["title"]} · 347 模拟题</title>{STYLE}</head>'
            f'<body><div class="wrap">{"".join(parts)}</div></body></html>')


def topics_of(m):
    out = []
    for sec in m["sections"]:
        for it in sec["items"]:
            out.append(it["q"].splitlines()[0][:26].rstrip("？?。"))
    return "、".join(out)


def main():
    files = sorted(MOCKS.glob("mock-*.json"))
    cards = []
    for f in files:
        m = json.loads(f.read_text(encoding="utf-8"))
        (MOCKS / (f.stem + ".html")).write_text(build_page(m), encoding="utf-8")
        cards.append(
            f'<a class="card" href="mocks/{f.stem}.html"><b>{m["title"]}</b>'
            f'<span>{m["date"]}</span><em>{topics_of(m)}</em></a>')
    idx = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>云师大 347 模拟题 · 总目录</title>{STYLE}</head><body><div class="wrap">'
        '<h1>云师大 347 应用心理 · 模拟题总目录</h1>'
        '<div class="sub">每周一~五推送一套 | 每套 100 分 / 建议限时 90 分钟 | 题目 + 标准答案</div>'
        '<div class="tips">📝 建议：先独立限时作答，再点进页面看第二部分答案；答完把错题考点回到《每日一课》对应课程复习。</div>'
        f'<div class="grid">{"".join(cards)}</div>'
        '<div class="foot">按云师大历年真题结构编拟 · 押题遵循：统计测量必含 / 近 3 年原题避开 / 优先历史高频回考考点</div>'
        '</div></body></html>')
    (ROOT / "index.html").write_text(idx, encoding="utf-8")
    print(f"已渲染 {len(files)} 套模拟题 + index.html")


if __name__ == "__main__":
    main()
