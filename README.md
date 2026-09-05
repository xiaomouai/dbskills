# dbskills

从需求与流量、内容、线索、销售、交付到复购的通用商业闭环项目。适用于C端或B端产品、App、SaaS、课程和服务。

## content-revenue-loop

`content-revenue-loop` 帮助任意产品或服务建立“需求—流量—内容—销售—交付—复购”的可验证闭环。它会先定位最早断点，再完成当前一项任务，避免用曝光或内容数量代替商业结果。

将 `skills/content-revenue-loop` 放入支持 Agent Skills 的客户端后，可直接发送：

```text
使用 content-revenue-loop，为我的产品检查流量、内容和销售闭环，找出最早断点，并给出一轮可验证行动。
```

## 工作台

工作台用 Python 标准库保存业务真源、任务依赖、Agent 提示词和验收状态，不需要安装依赖。

```bash
python3 workbench.py init
python3 workbench.py plan --request "为我的产品建立商业闭环" --mode full --track consumer
python3 workbench.py status
python3 workbench.py verify
```

企业产品使用 `--track business`。打开 `runtime/index.html` 查看状态。每个任务按 `start → 生成产物 → complete` 登记；具体命令见[使用说明](docs/usage.md)。

仓库不提交实际运行产生的 `runtime/`，防止客户资料、内容和订单进入版本库。

## 项目结构

```text
skills/content-revenue-loop/SKILL.md  通用Agent入口
workbench.py                          本地任务和状态工作台
test_workbench.py                     最小行为测试
docs/architecture.md                  闭环和角色边界
docs/usage.md                         命令与宿主使用方法
```

## 设计参考

任务编排、明确 Skill 边界与本地真源的设计思路参考了 [dontbesilent2025/dbskill](https://github.com/dontbesilent2025/dbskill)。本仓库内容为针对“流量—内容—销售—交付—复购”闭环重新编写的独立实现，没有复制其知识库或 Skill 正文。使用参考项目内容时请遵守其 [CC BY-NC 4.0](https://github.com/dontbesilent2025/dbskill/blob/main/LICENSE) 许可证。
