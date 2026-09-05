# 使用说明

## 初始化和计划

```bash
python3 workbench.py init
python3 workbench.py plan --request "为产品建立流量、内容和销售闭环" --mode full --track consumer
```

`consumer` 用于C端，`business` 用于B端。初始化后编辑 `runtime/business.json`，补齐真实产品、付款人、购买场景、报价、证据和渠道。

模式：`full` 建完整闭环；`content` 在定位明确后制作并验收内容；`diagnose` 定位断点并形成调整策略。

## 执行任务

```bash
python3 workbench.py status
python3 workbench.py start research
python3 workbench.py complete research --output artifacts/01-research.md
python3 workbench.py block research --reason "缺少真实客户资料"
python3 workbench.py verify
```

`runtime/prompts/` 保存每个角色的任务说明。产物必须位于 runtime 内且非空；依赖未完成时不能启动下游任务。默认不覆盖已有计划，新项目使用 `--root <新目录>`。

## Agent客户端

把 `skills/content-revenue-loop` 安装或软链接到客户端的 Skill 目录，然后直接描述产品和目标。支持多 Agent 的客户端可以按依赖派发；不支持时顺序执行。终端不可用时仍可使用 Skill，但状态不会自动写入工作台，必须明确说明。

任何发布、外联、投流、订单或客户数据处理仍以用户授权和平台能力为准。
