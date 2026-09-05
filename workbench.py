#!/usr/bin/env python3
"""Local task ledger for the content acquisition multi-agent workflow."""
import argparse, html, json, os, sys
from datetime import datetime
from pathlib import Path

AGENTS = [
    ("research", "需求与流量Agent", [], "01-research.md", "验证付款人、购买场景、需求证据和流量入口"),
    ("strategy", "商业策略Agent", ["research"], "02-strategy.md", "确定产品、报价、渠道和停止条件"),
    ("content", "内容Agent", ["strategy"], "03-content.md", "产出与购买场景相连的可审核内容"),
    ("sales", "销售Agent", ["strategy"], "04-sales.md", "设计线索资格、报价、跟进和收款路径"),
    ("delivery", "交付与复购Agent", ["sales"], "05-delivery.md", "设计验收、成本、退款、复购和转介绍"),
    ("review", "验收Agent", ["content", "delivery"], "06-verification.md", "核验事实、依赖、漏斗关联和结果口径"),
]
TRACKS = {
    "consumer": {"name":"C端产品或服务","buyer":"个人消费者或实际付款人","metrics":["有效咨询/体验","首次付费","退款","使用/交付","复购"]},
    "business": {"name":"B端产品或服务","buyer":"企业决策人或预算负责人","metrics":["合格线索","演示/试点","签约回款","激活/交付","续费"]},
}

def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def read(path): return json.loads(path.read_text("utf-8"))
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", "utf-8")
    os.replace(tmp, path)
def paths(root): return root/"business.json", root/"tasks.json"

def init(root):
    root.mkdir(parents=True, exist_ok=True); business, tasks = paths(root)
    if not business.exists():
        write(business, {"active_track":"待选择：consumer 或 business","tracks":TRACKS,"product":"待填写","payer":"待填写","purchase_scenario":"待填写","offer":"待填写","price":"待填写","proof":[],"channels":[],"updated_at":now()})
    if not tasks.exists(): write(tasks, {"request":None,"created_at":now(),"tasks":[]})
    dashboard(root); print(f"工作台已初始化：{root}")

def plan(root, request, mode, track):
    init(root); _, taskfile = paths(root); data = read(taskfile)
    if data["tasks"]: raise ValueError("已有任务计划；请完成或使用新的 runtime 目录")
    business=read(paths(root)[0]); chosen=track or business.get("active_track")
    if chosen not in TRACKS: raise ValueError("请用 --track 选择 consumer 或 business")
    business["active_track"]=chosen; business["updated_at"]=now(); write(paths(root)[0],business)
    selected = AGENTS if mode == "full" else ([AGENTS[2], AGENTS[5]] if mode == "content" else [AGENTS[0], AGENTS[1], AGENTS[5]])
    selected_ids = {x[0] for x in selected}; (root/"prompts").mkdir(exist_ok=True); (root/"artifacts").mkdir(exist_ok=True)
    tasks=[]
    for task_id, role, deps, output, goal in selected:
        deps=[d for d in deps if d in selected_ids]
        task={"id":task_id,"role":role,"goal":goal,"status":"pending","dependencies":deps,"expected_output":f"artifacts/{output}","output":None,"reason":None,"updated_at":now()}
        tasks.append(task)
        prompt=f"# {role}\n\n业务线：{TRACKS[chosen]['name']}（{chosen}）\n用户任务：{request}\n\n业务档案：{root/'business.json'}\n任务台账：{taskfile}\n依赖：{', '.join(deps) or '无'}\n目标：{goal}\n交付：{root/task['expected_output']}\n\n只围绕当前业务线。读取业务档案和已完成依赖产物。事实、推断和未知项分开；缺资料不得编造。优先检查指标：{', '.join(TRACKS[chosen]['metrics'])}。只完成本角色任务，不发布、不外联、不投流。完成后由总控登记产物。\n"
        (root/"prompts"/f"{task_id}.md").write_text(prompt,"utf-8")
    write(taskfile,{"request":request,"mode":mode,"track":chosen,"created_at":now(),"tasks":tasks}); dashboard(root); print(json.dumps(tasks,ensure_ascii=False,indent=2))

def get_task(data, task_id):
    for task in data["tasks"]:
        if task["id"]==task_id:return task
    raise ValueError(f"未知任务：{task_id}")

def change(root, action, task_id, output=None, reason=None):
    _, taskfile=paths(root); data=read(taskfile); task=get_task(data,task_id)
    if action=="start":
        incomplete=[d for d in task["dependencies"] if get_task(data,d)["status"]!="completed"]
        if incomplete: raise ValueError("依赖尚未完成："+", ".join(incomplete))
        task["status"]="running"
    elif action=="complete":
        target=(root/output).resolve(); base=root.resolve()
        if base not in target.parents or not target.is_file() or target.stat().st_size==0: raise ValueError("产物必须是 runtime 内存在的非空文件")
        task.update(status="completed",output=str(target.relative_to(base)),reason=None)
    else: task.update(status="blocked",reason=reason or "未说明原因")
    task["updated_at"]=now(); write(taskfile,data); dashboard(root); print(f"{task_id}: {task['status']}")

def verify(root):
    _, taskfile=paths(root); data=read(taskfile); errors=[]
    if not data["tasks"]: errors.append("没有任务计划")
    for task in data["tasks"]:
        if task["status"]=="completed":
            if not task["output"] or not (root/task["output"]).is_file(): errors.append(f"{task['id']} 缺少产物")
            for dep in task["dependencies"]:
                if get_task(data,dep)["status"]!="completed": errors.append(f"{task['id']} 的依赖 {dep} 未完成")
        else: errors.append(f"{task['id']} 状态为 {task['status']}")
    result={"structural_verification":"PASS" if not errors else "FAIL","errors":errors,"market_validation":"未验证；需真实公开内容、有效咨询、报价和已收款数据"}
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if not errors else 1

def dashboard(root):
    business_path, taskfile=paths(root)
    business=read(business_path) if business_path.exists() else {}; data=read(taskfile) if taskfile.exists() else {"request":None,"tasks":[]}
    rows=[]
    for t in data["tasks"]:
        link=f'<a href="{html.escape(t["output"])}">查看产物</a>' if t.get("output") else "—"
        rows.append(f'<tr><td>{html.escape(t["role"])}</td><td>{html.escape(t["status"])}</td><td>{html.escape(", ".join(t["dependencies"]) or "无")}</td><td>{link}</td></tr>')
    fields="".join(f"<li><b>{html.escape(str(k))}</b>：{html.escape(str(v))}</li>" for k,v in business.items() if k!="updated_at")
    doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>内容获客工作台</title><style>body{{max-width:920px;margin:40px auto;padding:0 18px;font:16px/1.6 system-ui;color:#172033}}h1{{color:#163d73}}section{{background:#f6f3ea;padding:18px;margin:16px 0;border-radius:12px}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;border-bottom:1px solid #ccd3dc;padding:9px}}code{{background:#e8edf3;padding:3px 6px}}@media(max-width:600px){{table{{font-size:13px}}}}</style><h1>内容获客工作台</h1><section><h2>当前任务</h2><p>{html.escape(str(data.get("request") or "尚未建立计划"))}</p></section><section><h2>业务档案</h2><ul>{fields}</ul><p>直接编辑 <code>business.json</code> 补齐真实资料。</p></section><section><h2>多 Agent 任务</h2><table><tr><th>角色</th><th>状态</th><th>依赖</th><th>结果</th></tr>{''.join(rows)}</table></section><section><h2>入口</h2><p><code>python3 workbench.py --root runtime status</code></p><p>让 Codex 使用项目中的 omnichannel-acquisition Skill，并说出一个真实内容获客任务。</p></section></html>'''
    (root/"index.html").write_text(doc,"utf-8")

def status(root): print(json.dumps(read(paths(root)[1]),ensure_ascii=False,indent=2))
def main():
    p=argparse.ArgumentParser(description="内容获客多Agent任务工作台"); p.add_argument("--root",type=Path,default=Path(__file__).parent/"runtime")
    sub=p.add_subparsers(dest="cmd",required=True); sub.add_parser("init")
    q=sub.add_parser("plan"); q.add_argument("--request",required=True); q.add_argument("--mode",choices=["full","content","diagnose"],default="full"); q.add_argument("--track",choices=list(TRACKS))
    sub.add_parser("status");
    for name in ("start","complete","block"):
        q=sub.add_parser(name); q.add_argument("id"); q.add_argument("--output" if name=="complete" else "--reason",required=name!="start")
    sub.add_parser("verify"); sub.add_parser("dashboard")
    a=p.parse_args(); root=a.root.resolve()
    try:
        if a.cmd=="init":init(root)
        elif a.cmd=="plan":plan(root,a.request,a.mode,a.track)
        elif a.cmd=="status":status(root)
        elif a.cmd in ("start","complete","block"):change(root,a.cmd,a.id,getattr(a,"output",None),getattr(a,"reason",None))
        elif a.cmd=="verify":sys.exit(verify(root))
        else:dashboard(root); print(root/"index.html")
    except (ValueError,FileNotFoundError,json.JSONDecodeError) as e: print(f"错误：{e}",file=sys.stderr); sys.exit(2)
if __name__=="__main__":main()
