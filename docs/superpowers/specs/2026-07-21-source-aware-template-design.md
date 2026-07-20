# 来源感知条件模板设计

## 目标

自定义视频模板继续使用 `${标题}`、`${链接}`、`${封面}` 等现有变量，并增加受限的 `{% if %}` 条件语法。模板根据原始消息来源选择回复内容：小程序卡片避免重复视频摘要，普通链接回复 BV 号，裸 BV 号回复视频链接。

## 已验证的输入结构

NapCat 与 AstrBot 的运行日志给出两种稳定结构：

- QQ 小程序通过 OneBot `json` 消息段进入 AstrBot，payload 包含 `app: com.tencent.miniapp_01`、`meta.detail_1.qqdocurl`，AstrBot 消息链保留 `Json` 组件。
- 普通分享链接通过 OneBot `text` 消息段进入 AstrBot，文本包含完整链接或 `b23.tv` 短链接。

裸 BV 号由原始纯文本完整匹配 `BV` 加 10 位字母数字判定。包含 BV 号的完整 URL 优先归类为链接。

## 来源模型

入口处理器在短链展开和 API URL 归一化之前计算 `source`：

- `card`：消息链存在可提取 Bilibili URL 的 `Json` 卡片。
- `url`：原始纯文本包含受支持的 Bilibili URL 或短链接。
- `bvid`：原始纯文本去除首尾空白后是单独的 BV 号。
- `text`：其他已被插件识别的纯文本形式，例如带说明文字的 BV 号。

分类优先级为 `card`、`url`、`bvid`、`text`。`source` 作为函数参数从 `on_message` 传入 `bili_keyword`、`video_detail` 和模板渲染函数，避免并发事件共享可变的来源状态。搜索命令使用 `source="url"`，因为搜索结果以解析所得视频 URL 进入详情流程。

## 模板语法

保留现有 `${变量}` 替换规则，新增以下控制标签：

```jinja2
{% if source == "card" %}
...
{% elif source == "url" %}
...
{% elif source == "bvid" %}
...
{% else %}
...
{% endif %}
```

控制语法仅支持：

- `{% if source == "值" %}`
- `{% elif source == "值" %}`
- `{% else %}`
- `{% endif %}`

值限定为 `card`、`url`、`bvid`、`text`。允许嵌套条件没有实际需求，本版本采用单层条件块。模板没有控制标签时保持原有行为。

推荐模板：

```jinja2
{% if source == "card" %}
🔗 ${链接}
{% elif source == "url" %}
${BV号}
{% elif source == "bvid" %}
${链接}
{% else %}
🎬 ${标题}
👤 ${UP主}
${封面}
🔗 ${链接}
{% endif %}
```

## 渲染流程

1. `_classify_message_source` 根据原始文本和卡片提取结果返回来源。
2. `_render_conditionals` 解析条件标签，只保留当前来源选中的文本分支。
3. `_apply_template` 对选中分支执行现有 `${变量}` 替换。
4. `${封面}` 在选中分支中继续拆分为独立图片组件；未选中的 `${封面}` 不生成图片。

## 错误处理

条件解析器遇到未知来源值、标签顺序错误、重复 `else`、缺失 `endif` 或控制标签之外的表达式时抛出明确的模板语法异常。视频详情层记录错误日志并回退到插件原始视频格式，保证解析回复仍可发送。

## 配置与文档

`_conf_schema.json` 的自定义模板提示增加 `source` 值和条件语法示例。README 增加来源表、语法约束和推荐模板。CHANGELOG 记录来源感知条件模板功能。

## 测试范围

- JSON 小程序卡片分类为 `card`。
- 完整 URL 和短链接分类为 `url`。
- 裸 BV 号分类为 `bvid`。
- 带说明文字的 BV 号分类为 `text`。
- URL 中包含 BV 号时分类为 `url`。
- `if`、`elif`、`else` 分支按来源渲染。
- 无条件旧模板输出保持一致。
- 未选中分支中的 `${封面}` 不生成图片。
- 非法条件语法产生明确异常并触发原始格式回退。

