# March7th

崩坏：星穹铁道多功能机器人（开发中），目前支持账号绑定、信息查询、Wiki 查询等功能。

本项目基于 Nonebot2，通过 [nonebot-plugin-send-anything-anywhere](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere) 实现对 OneBot v11, OneBot v12, QQ Guild, Kaiheila 适配器的支持；使用 [nonebot-plugin-datastore](https://github.com/he0119/nonebot-plugin-datastore) 进行插件数据管理。

## 安装

使用 `git clone https://github.com/Mar-7th/March7th.git` 或 [下载压缩包](https://github.com/Mar-7th/March7th/archive/refs/heads/master.zip) 并解压，进入工程目录。

使用 `poetry install` 安装项目依赖。

使用 `nb datastore upgrade` 升级数据库。

配置协议实现端（如 `go-cqhttp` 可使用 `nb plugin install gocqhttp` 安装）。

使用 `nb run` 运行 Bot 程序。
