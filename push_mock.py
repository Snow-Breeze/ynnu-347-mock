#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每周一~五推送当天模拟题链接到邮箱（只发用户本人）"""
import datetime
import json
import os
import smtplib
import subprocess
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOCKS = ROOT / "mocks"
STATE_FILE = ROOT / "push_state.json"

SITE = os.environ.get("SITE_BASE", "https://snow-breeze.github.io/ynnu-347-mock").rstrip("/")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465") or 465)
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("TO_EMAIL", "").strip() or SMTP_USER
DRY_RUN = os.environ.get("DRY_RUN", "").strip() in ("1", "true", "yes", "on")

try:
    from zoneinfo import ZoneInfo
    CN = ZoneInfo("Asia/Shanghai")
except Exception:
    CN = None


def now_cn():
    if CN is not None:
        return datetime.datetime.now(CN)
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


STYLE = """
<style>
body{margin:0;background:#f6f3ec;}
.wrap{max-width:600px;margin:0 auto;background:#fffdf8;padding:26px 22px 34px;
 font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
 color:#2f2f2f;line-height:1.8;font-size:15.5px;}
h2{color:#1f5c3d;font-size:20px;margin:0 0 12px;padding-bottom:10px;border-bottom:2px solid #1f5c3d;}
.btn{display:block;text-align:center;background:#1f5c3d;color:#fff;text-decoration:none;
 padding:14px;border-radius:8px;font-size:16.5px;margin:20px 0;letter-spacing:1px;}
.info{background:#f2f7f3;border-left:4px solid #1f5c3d;padding:12px 16px;margin:16px 0;border-radius:0 6px 6px 0;font-size:14.5px;}
.tip{color:#7a6420;background:#fff8e6;border:1px solid #f0dfae;padding:10px 14px;border-radius:6px;font-size:14px;}
.meta{color:#8a8a8a;font-size:12.5px;margin-top:20px;padding-top:12px;border-top:1px dashed #ddd6c4;}
</style>
"""


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        subprocess.run(["git", "add", "push_state.json"], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=mock-bot",
                        "-c", "user.email=mock-bot@users.noreply.github.com",
                        "commit", "-m", f"push state {s.get('last_date')}"],
                       check=True, capture_output=True)
        try:
            subprocess.run(["git", "push"], check=True, capture_output=True)
        except Exception:
            url = os.environ.get("GIT_PUSH_URL", "")
            if url:
                subprocess.run(["git", "remote", "set-url", "origin", url], check=True, capture_output=True)
                subprocess.run(["git", "push"], check=True, capture_output=True)
            else:
                raise
    except Exception as e:
        print(f"[warn] state push failed: {e}")


def send(subject, html):
    if not TO:
        raise RuntimeError("TO_EMAIL / SMTP_USER 未配置")
    if DRY_RUN:
        print(f"[dry-run] would send: {subject} -> {TO} ({len(html)} chars)")
        return
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("云师大347模拟题", "utf-8")), SMTP_USER))
    msg["To"] = TO
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [TO], msg.as_string())
    print(f"sent: {subject} -> {TO}")


def main():
    today = now_cn().date()
    wd = "一二三四五六日"[today.weekday()]
    print(f"now(CN) {now_cn().isoformat(timespec='seconds')} | 周{wd} {today}")
    if today.weekday() >= 5:
        print("周末不发（周一~周五推送）")
        return

    target = None
    for f in sorted(MOCKS.glob("mock-*.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        if str(m.get("date")) == today.isoformat():
            target = (f.stem, m)
            break
    if not target:
        print(f"今天（{today}）没有排到的模拟题，跳过")
        return

    stem, m = target
    state = load_state()
    if state.get("last_date") == today.isoformat():
        print(f"今天已推送过（{state}），跳过")
        return

    link = f"{SITE}/mocks/{stem}.html"
    idx = f"{SITE}/index.html"
    topics = "、".join(it["q"].splitlines()[0][:20].rstrip("？?。")
                     for sec in m["sections"] for it in sec["items"])
    body = (
        f'<h2>📝 {m["title"]} · 今日模拟题</h2>'
        f'<div class="info"><b>日期</b>：{m["date"]}（周{wd}）<br>'
        f'<b>题量</b>：4 大题 / 满分 100 分<br>'
        f'<b>建议</b>：限时 90 分钟独立作答</div>'
        f'<a class="btn" href="{link}">👉 打开今日模拟题</a>'
        f'<div class="tip">做完再看页面第二部分的标准答案；错题考点建议回到《每日一课》对应课程复习一遍。</div>'
        f'<div class="info"><b>本套覆盖</b>：{topics}</div>'
        f'<div class="meta">全部模拟题目录：{idx}　|　本邮件只发给你本人</div>'
    )
    html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{STYLE}</head><body><div class="wrap">{body}</div></body></html>'
    send(f'【347模拟题】{m["title"]} · {today} 今日练习', html)

    if not DRY_RUN:
        save_state({"last_date": today.isoformat(), "no": m["no"], "stem": stem})


if __name__ == "__main__":
    main()
