# 来源、许可与公开规则

官方课程：https://cs329z.stanford.edu/
官方政策：https://cs329z.stanford.edu/logistics.html
官方 starter：https://github.com/cs329z/assignment1-harness
固定基准：c6cab03d161e4e8db8a9e2c12caf8e353b079beb

课程要求：HW1 从零构建企业邮件助手及 agent harness，不使用 agent 框架；后续包括工具、终端、记忆和人工确认。HW2 聚焦 Agent 评估。

2026-10-15 核查官网：允许在作业和项目中使用 AI 生成代码，要求能验证并解释；禁止抄取网上答案。没有在已查官网与 README 找到明确允许或禁止公开完整答案的条款。已完整提取官方 PDF v26.1.0 的26页文本，检索 honor/public/publish/share/solution/collaboration/license，并渲染核对第2、6、25页；未发现明确允许或禁止公开完整解答的条款，不能称公开许可已确认。AI 使用许可、starter 的 MIT 与完整作业解答的公开政策是不同问题。

官方 starter 许可证原文保留在 `hw1/LICENSE`，必须保留原版权归属。官方源文件不是个人原创。用户已明确授权新增代码采用MIT；根目录LICENSE保留cs329z和evanchai署名，上游原许可证同时保留于hw1/LICENSE。README如实说明AI辅助实现与贡献归属的不确定性，不宣称全部手写或所有设计均由用户独立完成。

本最新版保留MIT许可下的24份虚构公司文档、公开评分规范及安全fixtures；排除真实邮件档案、priority_gold.json、另3个含真实邮件地址的fixture、PDF/提取文本、模型缓存、runs和大视频。缺失fixture与档案可按官方固定版本另取，仅用于私有本机核验，勿混入公开准备稿。原始导出独立保留于证据目录。

用户已看过结构预览，并明确授权以public发布及为新增代码采用MIT。课程解答公开条款的不确定性继续如实披露，本稿不声称课程方已批准，也不把未知写成禁止。

## PDF核查补充（2026-10-15）

官方固定版手册：https://github.com/cs329z/assignment1-harness/blob/c6cab03d161e4e8db8a9e2c12caf8e353b079beb/cs329z_assignment1_harness.pdf

- 第2页：允许使用AI工具，要求能解释并对提交内容负责；这不是解答公开许可。
- 第5–6页：邮件库是2001年6–8月的真实Enron邮件切片，含26278封；另添加少量合成needle邮件。第6页提醒邮件由真实人物撰写，经联邦调查公开而非自愿公开，包含私人消息。此前图文把“虚构公司文档”和“邮件档案”合在一起不能理解为全部数据虚构。
- 第25页：提交到Gradescope的ZIP需排除.env、.lm_cache和data/emails，但需包含最终runs；这是提交规范，不是GitHub公开规范。公开学习仓库仍应排除含真实邮件或个人内容的runs。
- 第25页：致谢末尾声明作业MIT许可，并允许授课复用时简短署名；没有另列学生完整解答公开条款。不能把“未知”写成“禁止”。
- 文件420885字节，Git blob SHA1 2fbf507d43024991e54c1bcc89e2d692e6f9836c，与固定官方版本匹配。PDF只供核查，不加入候选仓库。
