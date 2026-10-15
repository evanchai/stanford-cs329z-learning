# Public 预览检查清单

2026-10-15：用户已审阅结构预览，明确选择public，并授权新增代码采用MIT。以下是发布快照的内容检查；实际远程状态以GitHub仓库为准。

## 当前已完成

- 所有P1–P14源码、adapters以及P15官方harness保留，原作业Python源码未改。P16/P17缺失在主README首屏明示。
- 根README提供实际结构、模块职责、两条阅读路线、题目映射、从零安装、无需API的离线入口和可选模型配置。
- 原官方README保存在hw1/UPSTREAM_README.md，新hw1/README明确原说明与精简快照的差异。
- 上游MIT版权全文和来源链接保留；官方、原Claude辅助实现、本轮整理分别标记。
- 未纳入.env、凭证、真实邮件档案、模型缓存、会话/记忆、原git补丁、私人聊天链接或大视频。
- 原恢复文档的本机路径、云端临时目录、私人会话链接已从本预览移除。官方源码中的通用系统路径和示例路径属于程序行为，不是用户机器位置。
- JUnit去除hostname及skip堆栈路径；新运行报告默认gitignore，发布时需单独审查失败详情。
- 有限模式扫描覆盖私钥、常见provider token、带凭证URL及JWT；0命中不等于证明不存在任何秘密。

## 已排除的数据及运行影响

|文件或目录|原因|影响|
|---|---|---|
|data/emails.jsonl.gz、data/emails/|真实Enron邮件档案|4个BM25档案测试跳过，live邮件能力不可完整复现|
|tests/fixtures/priority_gold.json|含60封真实邮件全文|P1 live accuracy不可直接运行|
|tests/fixtures/terminal_questions.json|含历史邮件地址|terminal live测试缺fixture|
|tests/fixtures/personas/09-coding-no-python.json|含历史邮件地址|公开persona集合减少|
|tests/fixtures/personas/20-coding-big-listing.json|含历史邮件地址|公开persona集合共18个，不能作为原20个的完整基准|
|作业PDF、hw1.txt|避免在学习仓库重复分发资料与示例地址|链接官方固定版本供阅读|
|runs、.lm_cache、私人记忆与原始对话|可能含邮件内容或私人信息|历史live结果只作记录，不能逐条重现|

原始导出和完整来源证据独立保留，不属于此public目录；没有为脱敏修改官方题目或伪造替代测试数据。取回缺失项时应放到单独私有工作副本。不要直接把精简的18个persona评测当成20-persona结果。

## 尚未完成与发布边界

1. 用户已看过结构预览并授权发布；发布范围仅为此清理后的快照。
2. 课程官网/手册允许AI辅助、要求理解并禁止查阅网上答案；未找到明确的学生完整解答公开条款。已披露不确定性，不声称官方批准或禁止。用户选择public没有改变课程政策的事实状态。
3. 上游MIT归属保留；新增实现及本轮工具按用户授权使用MIT，见LICENSE和THIRD_PARTY_NOTICES.md。
4. P16/P17未完成，不能称“全作业完成”。282/4仅确定性核验，不是课程成绩。终端隔离、防注入与记忆缺陷见AUDIT；作为学习快照展示，不作为生产安全Agent。

结论：**此快照按公开学习项目范围整理；不是完整作业提交或生产就绪项目。**
