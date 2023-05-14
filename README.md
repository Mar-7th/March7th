# March7th

崩坏：星穹铁道多功能机器人（开发中），目前支持账号绑定、信息查询、Wiki 查询等功能。

本项目基于 Nonebot2，通过 [nonebot-plugin-send-anything-anywhere](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere) 实现对 OneBot v11, OneBot v12, QQ Guild, Kaiheila 适配器的支持；使用 [nonebot-plugin-datastore](https://github.com/he0119/nonebot-plugin-datastore) 进行插件数据管理。

## 安装

使用 `git clone https://github.com/Mar-7th/March7th.git` 或 [下载压缩包](https://github.com/Mar-7th/March7th/archive/refs/heads/master.zip) 并解压，进入工程目录。

使用 `poetry install` 安装项目依赖。

使用 `nb datastore upgrade` 升级数据库。

配置协议实现端（如 `go-cqhttp` 可使用 `nb plugin install gocqhttp` 安装）。

配置运行环境参数（可复制 `.env` 文件到 `.env.prod` 后填入参数）。

安装 [汉仪润圆-65W](https://www.hanyi.com.cn/productdetail?id=657) 字体，若不安装则使用系统已安装字体制图，但响应较慢。

使用 `nb run` 运行 Bot 程序。

发送命令 `srhelp` 即可查看命令列表。

## 常见问题

- 添加公共 cookie：

  - 只有添加公共 cookie 后才可以不需要用户绑定 cookie 就能查询 `srinfo`
  - 添加公共 cookie 需要 `SUPERUSER` 权限，发送 `srpck [cookie]`

- 安装字体后仍显示为原字体：可删掉 `matplotlib` 字体缓存文件重新运行
  缓存文件位置：

  - Windows: `C:\Users\<username>\.matplotlib\fontlist-xxx.json`
  - Linux: `~/.cache/matplotlib/fontlist-xxx.json`
  - Mac: `~/Library/Caches/matplotlib/fontlist-xxx.json`

## 链接

本项目基于以下项目完成：

| 项目 / 插件名                                                                              | 描述                                            | 使用方式            |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------- | ------------------- |
| [`Mar-7th/StarRailRes`](https://github.com/Mar-7th/StarRailRes)                            | 崩坏：星穹铁道资源库                            | Icon 及攻略资源     |
| [`CMHopeSunshine/LittlePaimon`](https://github.com/CMHopeSunshine/LittlePaimon)            | 小派蒙！基于 Nonebot2 的原神 QQ 机器人          | 米游社 API 接口参考 |
| [`MeetWq/pil-utils`](https://github.com/MeetWq/pil-utils)                                  | A simple PIL wrapper and text-to-image tool     | PIL 绘图辅助工具    |
| [`nonebot/nonebot2`](https://github.com/nonebot/nonebot2)                                  | 跨平台 Python 异步聊天机器人框架                | Bot 框架            |
| [`nonebot_plugin_saa`](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere) | 一个帮助处理不同 Adapter 消息的适配和发送的插件 | Bot 消息发送实现    |
| [`nonebot_plugin_datastore`](https://github.com/he0119/nonebot-plugin-datastore)           | 适用于 NoneBot2 的数据存储插件                  | Bot 插件数据管理    |
