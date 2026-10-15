# HW1 恢复与源码审查

核验日期：2026-10-15。审查和文档整理没有修改原作业Python代码。

## 来源与完整性

源码从原AI辅助作业工作区导出；私人对话链接、临时容器位置及本机路径留在私有恢复记录，未纳入此公开预览。

导出记录：main @ `d5d6a41693b872ea518f3a9a76fc85ad6e531eb0`，基准 `c6cab03d161e4e8db8a9e2c12caf8e353b079beb`，后续24提交。记录中的remote为 https://github.com/cs329z/assignment1-harness ，工作树无tracked改动，只有未跟踪hw1.txt。导出未包含.git，因此这些git状态为导出记录，不能当作本机live git查询。本准备目录也未初始化.git。

原始ZIP（未纳入本目录）：831302字节。SHA-256：

`e197054cfea8783704d2aefa8799c815ec114ac3731b466427dfd6b5630403a9`

ZIP共143条目（含目录），实际文件129个（含校验清单）；无绝对路径、..路径或符号链接。内部128项校验全部匹配。将24提交的main补丁按倒序反向应用到临时副本后，107个保留的官方文件全部匹配固定基准Git blob，0不符；唯一额外文件hw1.txt。官方109文件中另2个（真实邮件压缩档、priority_gold.json）按规则未导出。证据在reports/provenance-check.json。

## 实现范围

|题目|实际实现|本机验证|
|---|---|---|
|P1 priority|评分规范提示词、严格JSON分类，异常归unknown|25 deterministic通过|
|P2 digest|并发分类，只把urgent邮件送给摘要模型|8通过|
|P3 BM25|倒排表、Lucene IDF、k1=1.5/b=0.75、按分数及ID排序|14通过；4档案测试跳过|
|P4 email QA|预规划与迭代检索两方案；默认最多3次搜索，过滤未返回的support ID|12通过|
|P5 registry|JSON Schema参数校验、执行与异常反馈|44通过|
|P6 protocol|提示词渲染、JSON工具调用格式、容错解析与外来工具语法纠错|60通过|
|P7 loop|模型→解析→验证→执行→观察循环，预算和错误停止状态|31通过|
|P8 Cardinal|邮件工具与公司文档、终端、记忆等工具整合；邮件索引懒加载|5通过|
|P9 docs|150-token按行/章节切块，BM25、章节和日期元数据、600-token分页读取|36通过|
|P10 terminal|调用课程sandbox，返回退出码/标准输出/错误，长输出头尾截断及落盘|9通过|
|P11 compaction|80%预算触发辅助模型摘要、原用户约束逐字pin、必要时硬裁剪|6通过|
|P12 memory|JSON持久化、加载全部记忆、辅助模型选择被修正事实、词重叠召回|7通过|
|P13 interactive|confirm/auto模式、批准/拒绝、用户steering和澄清工具|15通过|
|P14 guards|固定deny regex、拒绝与工具数据中逐字相同的命令；CHECK_B=False|10通过|
|P15 sim eval|课程提供simulation harness使用上述agent，无单独学生实现文件|本轮未运行；历史脱敏汇总18/20|
|P16 field notes|缺field_notes.pdf和所需个人交互记录|未完成|
|P17 design memo|只有notes/design_log.md素材，缺design_memo.pdf|未完成|

adapters均已连接实现。源码有过期“placeholder”注释，但相关实际工具函数已经实现；不能只凭注释判断未完成。

## 本轮测试与复现

使用临时Python3.11.15环境；依赖版本见tools/audit-requirements.txt。依赖从PyPI安装，未改变系统Python。测试在默认执行沙箱内运行，没有为执行学生代码提升权限。仅依赖下载因DNS限制获得网络执行许可。

执行前检查了conftest的.env加载、llm初始化、terminal及sandbox的子进程路径。tools/audit_offline.py在独立进程中禁用.env加载、禁止LM构造和真实调用、通过audit hook拒绝网络连接/DNS；进程用env -i清空继承凭证，禁止pytest外部插件自动加载。不修改作业源码。

运行官方非live测试，排除整个test_sim_eval.py，缺archive的4项跳过。结果：286项执行记录，282通过、4跳过、0失败/错误。真实LM/网络尝试均0。终端测试只执行已检查过的脚本化echo、读写临时文件、打印、退出码和超时样例。未启动Claude/Codex订阅CLI、外部模型或模拟评测。

本机结果日志和去除hostname的JUnit保存在reports/。59个原始Python文件语法均可解析。未验证真实LLM质量、完整邮件检索性能、课程held-out模型或P15最新HEAD的表现。

当前可移植的安装与离线复现步骤见README。报告中的282/4来自首次恢复核验；公开预览的说明和工具整理有独立复核记录，不等同真实模型性能。

## 关键改进与风险

1. **终端隔离是主要生产风险。** 课程sandbox.jail()在OS jail不可用/探测失败时回退none；命令allowlist允许python/tee等，不能单独提供文件隔离。原日志明确记录Linux容器曾写到workspace之外。本轮测试通过不证明部署环境安全；展示前应改成隔离不可用就拒绝执行，并验证真实文件和网络边界。
2. **防注入仍是启发式。** CHECK_B明确关闭；逐字命令匹配不能阻止改写、编码或从终端输出转来的攻击，系统提示词不是安全边界。不能宣传成生产安全沙箱。
3. **记忆修正与污染。** 旧事实删除依赖辅助模型；新事实自身仍可能包含旧数值。历史P15两项失败分别是poisoned-policy和corrected-number。拒绝记忆保存整段命令而非仅稳定偏好，可能长期带入危险/敏感内容。并发锁为实例级，多个MemoryStore实例可能覆盖彼此写入。
4. **解析和预算边界。** protocol以truthiness判断use_tool而非严格bool；BM25负k使用Python负切片；单条过长current user/system prompt在无可裁剪消息时仍可能超上下文。现有公开测试不覆盖这些全部边界。
5. **生成质量与泛化。** priority严格JSON拒绝fences；digest不传日期，300词仅靠prompt；QA正文截断1500字符、support ID合法不等于答案忠实。日志曾用测试样例调prompt后弃用，仍不能把反复调公开测试集结果宣传为未见数据泛化。
6. **后端扩展单独说明。** backends.py使订阅CLI作为模型入口，语义与课程模型不同；Codex read-only不等于禁用工具。成本记0只表示该ledger未计费，不能证明无使用额度或机会成本。评分会替换llm.py等provided文件。

## 发布与贡献

目前适合学习展示，尚不宜原样作为完整成品公开。最小完善：补充自己的设计解释/P16–P17、把离线证据写进README、独立验证终端隔离和记忆修正、用合成数据演示，再核实课程完整答案公开政策。

AI生成实现的参与有原对话和提交补丁支持；多处注释/日志把设计标为Ning选择，但其本身是Claude撰写，不能独立证实逐行作者或每个设计决策归属。不要自称全部手写。课程提供的harness、测试和资料也不是个人原创。

原导出扫描常见私钥/provider token/credential URL/JWT模式0命中，未见.env、邮件档案、缓存、runs或视频；扫描不等于全面保证。额外发现personas/20-coding-big-listing.json也含真实邮件地址（原清单只明确提到另外2处）；准备稿把这3个fixture、PDF与hw1.txt都排除，原始证据保持不变。上游MIT归属保留，新增代码已获用户授权采用MIT。完整git补丁含放弃分支和历史提示词，仅作为私有恢复证据保留，不直接加入发布准备目录。
