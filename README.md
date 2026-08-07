<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_bili_resolver?name=astrbot_plugin_bili_resolver&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_bili_resolver

_✨ bilibili小组件等转链的工具 ✨_

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-4.0%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-chufeng-blue)](https://github.com/chufeng)

</div>

AstrBot 插件 —— 自动解析群聊/私聊中的 B 站链接，返回视频信息摘要。

> 本插件主要是为了避免转链容易被 QQ 踢下线的情况，本人从插件发布到现在还未被踢下线。

## 效果示例

群里有人发了一个 B 站链接或小程序卡片，机器人自动回复：

```
https://www.bilibili.com/video/av114556558967080?p=1

标题："终于知道为什么听到某些歌，反派会愣住了。因为...这也是他们的童年啊..."
小标题：TG-2025-05-23-175551094
类型：XX | UP：一罐蠢乃酱 | https://space.bilibili.com/3546772907493433

播放：359.35万 | 弹幕：2350 | 收藏：12.97万
点赞：28.47万 | 硬币：4.07万 | 评论：2422

简介：-
```

同时附带视频封面图。

## 支持的链接格式

| 类型 | 示例 |
|------|------|
| 短链 | `https://b23.tv/xxx` |
| 视频 | `bilibili.com/video/av...` 或 `BV...` |
| 番剧 | `bilibili.com/bangumi/play/ep...` / `ss...` / `md...` |
| 专栏文章 | `bilibili.com/read/cv...` |
| 动态 | `bilibili.com/opus/...` 或 `t.bilibili.com/...` |
| QQ 小程序卡片 | 分享 B 站内容到 QQ 的卡片消息 |

## 指令

| 指令 | 说明 |
|------|------|
| `/搜视频 关键词` | 搜索 B 站视频，返回第一个结果的解析信息 |

## 安装

**推荐**：在 AstrBot WebUI 的插件管理页面，搜索 `astrbot_plugin_bili_resolver` 一键安装。

手动安装：将插件目录放入 AstrBot 的 `data/plugins/` 目录下，重启或热重载即可。

## 配置

安装后可在 AstrBot WebUI 插件管理面板中修改，无需编辑文件。

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| `enable_auto_parse` | bool | `true` | 自动解析开关 |
| `enable_search` | bool | `true` | `/搜视频` 指令开关 |
| `enable_image` | bool | `true` | 回复中是否显示封面图 |
| `group_whitelist_mode` | bool | `false` | 白名单模式（开启=仅列表中的群生效，关闭=黑名单模式） |
| `group_list` | list | `[]` | 群组 ID 列表 |
| `template_preset` | string | `原始格式` | 视频解析排版风格，见下方说明 |
| `video_template` | text | `` | 自定义排版模板，仅在 `template_preset` 为 `自定义` 时生效 |

**白名单模式**：只有列表中的群触发，其他群忽略。
**黑名单模式**（默认）：列表中的群不触发，其他群正常。列表为空则所有群生效。

### 视频排版风格

通过 `template_preset` 选择视频解析的输出格式：

**原始格式**：插件内置的纯文字格式。

```
https://www.bilibili.com/video/av114556558967080

标题："终于知道为什么听到某些歌，反派会愣住了"
类型：综合 | UP：一罐蠢乃酱 | https://space.bilibili.com/xxx

播放：359.35万 | 弹幕：2350 | 收藏：12.97万
点赞：28.47万 | 硬币：4.07万 | 评论：2422

简介：-
```

**简洁风格**：带 Emoji 的卡片格式，同时附带封面图。

```
🎬 标题：终于知道为什么听到某些歌，反派会愣住了
👤 UP主：一罐蠢乃酱
📝 简介：-
[封面图]
👍 点赞：28.47万 🪙 投币：4.07万
❤️ 收藏：12.97万 🔄 转发：1234
👀 观看：359.35万 💬 弹幕：2350
```

**自定义**：在 `video_template` 文本框中填入自定义模板，使用变量占位符自由排版。

支持的变量：

| 变量 | 说明 |
|------|------|
| `${标题}` | 视频标题 |
| `${UP主}` | UP 主名称 |
| `${UP主链接}` | UP 主空间链接 |
| `${简介}` | 视频简介（最多 3 行） |
| `${封面}` | 封面图（渲染为图片，受「显示封面」开关控制） |
| `${点赞}` | 点赞数 |
| `${投币}` | 投币数 |
| `${收藏}` | 收藏数 |
| `${转发}` | 转发数 |
| `${观看}` | 播放数 |
| `${弹幕数量}` | 弹幕数 |
| `${评论}` | 评论数 |
| `${链接}` | 视频链接 |
| `${发布时间}` | 发布时间 |
| `${类型}` | 视频分区 |
| `${BV号}` | BV 号 |
| `${时长}` | 视频时长（格式：`m:ss` / `h:mm:ss`） |
| `${版权}` | 原创 / 转载 |

#### 按消息来源控制模板

自定义模板支持来源条件：

| `source` 值 | 原始消息 |
|--------------|----------|
| `miniapp` | QQ 小程序（`com.tencent.miniapp_01`） |
| `card` | QQ 图文卡片（`com.tencent.tuwen.lua`） |
| `url` | 完整链接或短链接 |
| `bvid` | 单独发送的 BV 号 |
| `text` | 其他可识别文本，例如带说明文字的 BV 号 |

支持 `{% if %}`、`{% elif %}`、`{% else %}`、`{% endif %}`。每个控制标签独占一行，条件值使用上表中的五个固定值。含条件标签的模板会移除渲染结果末尾、紧邻控制标签的换行；现有无条件模板保持原有输出。

下面的模板让小程序卡片只回复链接，链接只回复 BV 号，裸 BV 号只回复链接：

```jinja2
{% if source == "miniapp" %}
🔗 ${链接}
{% elif source == "card" %}
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

条件语法错误会写入 AstrBot 日志，并自动使用原始格式完成本次回复。

## 依赖

- Python >= 3.10
- AstrBot
- aiohttp
