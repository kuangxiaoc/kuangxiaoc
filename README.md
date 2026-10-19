<div align="center">

<br/>

<samp>HANGZHOU &nbsp;·&nbsp; LLM APPLICATION ENGINEERING &nbsp;·&nbsp; SINCE 2022</samp>

<br/><br/>

# 蔡 超

<samp>Xiao Cai &nbsp;/&nbsp; AI Agent 工程化 &nbsp;/&nbsp; LLM × 符号音乐</samp>

<br/>

浙江师范大学 · 电子信息（软件工程与大模型应用）在读<br/>
<a href="mailto:c1156269458@gmail.com">c1156269458@gmail.com</a> &nbsp;·&nbsp; <a href="https://github.com/kuangxiaoc">@kuangxiaoc</a>

<br/><br/>

</div>

---

<br/>

> 把大模型能力落到**能跑通、可验证、可维护**的系统里，<br/>
> 而不是停在 demo。

<br/>

## <samp>01</samp> &nbsp; 关于

本科人工智能，研究生转向软件工程与大模型应用。工作集中在三条线：

| | | |
| :-- | :-- | :-- |
| **编排** | Agent 工作流 | LangGraph / LangChain 状态机、工具调用、结果校验与重试，处理不确定的模型输出 |
| **摄入** | 文档结构化抽取 | PDF → 结构化数据，规则匹配与大模型判定结合，并发、限流、断点续跑 |
| **检索** | 图谱与双路召回 | 语义检索 + Cypher 图查询，补上纯向量检索缺失的结构信息 |

科研侧在 LLM 与音乐生成的交叉方向：用 Agent 从模型偏好排名中抽取可解释规则，再用确定性验证器自动验证与修复。

<br/>

## <samp>02</samp> &nbsp; 作品

<table>
<tr>
<td width="33%" valign="top">

<samp>2025.11 — </samp>

**CodeGraph Pilot**

基于 AST 静态分析与知识图谱的代码影响分析 Agent。Python `ast` → Neo4j 代码知识图谱，LangGraph 四阶段状态机（抽取 → 检索 → 生成 → 审查），以单一 MCP 工具对外暴露。

<samp>218 个离线单测 · 幻觉率 3.6% · grounding recall 100%（n=30）</samp>

</td>
<td width="33%" valign="top">

<samp>2026.01 — 2026.03</samp>

**建筑资料智能提取**

Agent 开发实习。独立开发「分类 → 识别 → 校验 → 抽取 → 合并」五步流水线，Asyncio 并发 + 缓存 / 限流 / 重试 / 断点续跑，动态数据模型支持多类资料。

<samp>LangChain · Pydantic · Asyncio</samp>

</td>
<td width="33%" valign="top">

<samp>2026.05</samp>

**音乐规则挖掘**

科研项目，已投稿。LLM-Agent 从神经网络偏好排名中自动提取可解释音乐规则；设计 BAR / Onset / Pitch / Duration 符号 Token 方案；确定性验证器闭环修复。

<samp>LLM-Agent · Tokenization · Verifier</samp>

</td>
</tr>
</table>

<br/>

## <samp>03</samp> &nbsp; 技术

| | |
| :-- | :-- |
| <samp>AGENT</samp> | LangGraph · LangChain · 工具调用 · 状态机编排 · Critic 校验 · 重试与工作流拆解 |
| <samp>RAG</samp> | RAG / GraphRAG · Neo4j · Cypher · 语义检索 · 图关系链路追踪 |
| <samp>CORE</samp> | Python · FastAPI · PostgreSQL · Pydantic · Asyncio · Docker · Git |
| <samp>MODEL</samp> | PyTorch · Transformer · REMI / 符号 Tokenization · RLHF / DPO 基础 |

<br/>

## <samp>04</samp> &nbsp; 开源

**[resume-builder](https://github.com/kuangxiaoc/resume-builder)** &nbsp;<samp>MIT</samp><br/>
跨 agent 简历生成 skill：按 JD 从个人 `profile.yaml` 裁剪改写，输出 1 页 A4 LaTeX 简历 PDF。支持 Claude Code / Codex / WorkBuddy，契约 / 模板 / 脚本三层拆分。

<br/>

## <samp>05</samp> &nbsp; 数据

<div align="center">

[![GitHub Roast 评分卡](https://ghfind.com/api/card/mini/kuangxiaoc?lang=zh)](https://ghfind.com/u/kuangxiaoc?ref=badge)

[![Tokens Stats](https://tokens.ci/api/embed/kuangxiaoc/svg?theme=light&template=graph&color=blue&today=1&rank=percent&tokens=compact&cost=compact)](https://tokens.ci/u/kuangxiaoc)

</div>

<br/>

---

<div align="center">

简历 PDF 可邮件索取，或用 <a href="https://github.com/kuangxiaoc/resume-builder">resume-builder</a> 自己跑一份。

<samp>LAST UPDATED &nbsp;2026 · 10</samp>

</div>
