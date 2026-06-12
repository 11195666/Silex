# Silex

Silex 是一个面向越狱 iOS 生态的静态 APT 源生成器。

在线 Demo：[repo.mjh.im](https://repo.mjh.im)

基于 [Silica](https://github.com/Shugabuga/Silica) v1.2.2 深度二次开发，专为现代越狱环境定制。保留了原版「静态生成、无后端」的核心模型，同时补齐了 rootless / roothide 支持、多版本共存、中英双语 UI、轻量 JSON API 等关键能力。

> 与上游的详细差异对比见 [ENHANCEMENTS.md](ENHANCEMENTS.md)。

## Demo

在线源：**[repo.mjh.im](https://repo.mjh.im)**

在 Sileo / Cydia / Zebra 中添加 `https://repo.mjh.im` 即可查看效果。

## 截图

| 首页 | 插件详情 |
|------|---------|
| ![首页](screenshots/homepage.png) | ![详情](screenshots/depiction.png) |

| Sileo 原生描绘 | 更新日志 |
|------|---------|
| ![原生](screenshots/native.png) | ![更新日志](screenshots/changelog.png) |

> 截图放至 `screenshots/` 目录即可。

## 特性亮点

- **完全静态输出**：产物可直接托管在 GitHub Pages 或任意静态服务器
- **rootless + roothide 双架构**：动态收集 arm64 / arm64e 架构，Release 文件自动生成
- **多版本共存**：同一包可保留多个历史版本，用户长按切换
- **tagline 自动注入 Description**：修改 `index.json` 即生效，无需重新 Theos make
- **中英双语详情页**：网页版与 Sileo 原生描绘均支持双语言
- **胶囊式详情页**：网页版带 tab 切换、暗黑模式、卡片式更新日志
- **个人名片式首页**：头像 + 源介绍 + 三个包管理器一键添加按钮
- **轻量 JSON API**：版本检测、包列表、搜索、精选、频道分组等接口
- **交互式编译脚本**：`ok.sh` 一步完成编译 → 发布流程
- **`description.md`**：每个包可写独立 Markdown 详情页，支持完整排版

## 项目结构

```text
Silex/
├── index.py                  # 主编译入口
├── Packages/                 # 插件目录（放包和元数据）
├── Styles/                   # 模板和品牌素材
├── util/                     # 编译器工具集
├── docs/                     # 编译产物（静态源）
├── ok.sh                     # 交互式编译发布脚本
└── requirements.txt          # Python 依赖
```

## 包目录结构

每个插件在 `Packages/` 下拥有独立目录：

```text
Packages/
├── 虚拟权限/                  # rootless 版本 (arm64)
│   ├── xxx_8.3.0_iphoneos-arm64.deb
│   ├── xxx_8.5.0_iphoneos-arm64.deb  ← 多版本共存，旧版本自动归档
│   └── silex_data/
│       ├── index.json
│       ├── description.md      # Markdown 详情描述
│       ├── icon.png
│       ├── banner.png
│       ├── screenshots/        # 截图轮播
│       └── scripts/            # 包维护脚本
│
├── 虚拟权限_Roothide/          # roothide 版本 (arm64e)
│   ├── xxx_8.6.0_iphoneos-arm64e.deb
│   └── silex_data/
│       ├── index.json          # bundle_id: xxx.roothide
│       └── …
│
└── 其他插件 …
```

注意事项：
- 同一包的 arm64 和 arm64e 版本需分目录存放
- roothide 目录的 `bundle_id` 需以 `.roothide` 结尾
- 旧版本 `.deb` 保留在目录中即可，编译时自动按版本排序

## 环境要求

### 系统依赖

macOS:

```bash
brew install dpkg zstd
```

Debian / Ubuntu:

```bash
sudo apt-get install dpkg-dev gnupg git xz-utils bzip2 zstd
```

### Python

- Python 3 及以上
- `pip`

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

## 源配置

主配置位于 `Styles/settings.json`：

```json
{
    "name": "Silex",
    "description": "A customizable static repository generated with Silex.",
    "tint": "#27BEF5",
    "cname": "repo.example.com",
    "maintainer": {
        "name": "Repo Maintainer",
        "email": "maintainer@example.com"
    },
    "social": [
        {
            "name": "Project Homepage",
            "url": "https://example.com"
        }
    ],
    "announcements": [
        {
            "level": "warning",
            "title": "兼容性提示",
            "message": "请替换为此源相关的公告信息。"
        }
    ],
    "automatic_git": "false",
    "footer": "{{repo_name}} · Updated {{silex_compile_date}}",
    "enable_gpg": "false"
}
```

### 关键字段说明

| 字段 | 说明 |
|------|------|
| `name` | 源显示名称 |
| `description` | 源简介描述 |
| `tint` | 默认主题色（Hex 格式） |
| `cname` | 公开域名，不含 `https://` |
| `maintainer` | 源维护者信息 |
| `social` | 源级社交链接，在支持页面展示 |
| `announcements` | 首页公告横幅 |
| `automatic_git` | 是否编译后自动 git 提交 |
| `enable_gpg` | 是否签名 `Release.gpg` |
| `footer` | Mustache 模板渲染的页脚文本 |

### 公告级别

`announcements[].level` 支持以下视觉级别：

- `info`
- `warning`
- `error`
- `success`

## 包元数据 (index.json)

每个包需提供 `silex_data/index.json`。

### 最小配置示例

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "简短描述文本。",
    "developer": {
        "name": "Example Developer"
    },
    "section": "Tweaks",
    "architecture": "iphoneos-arm64",
    "works_min": "15.0",
    "works_max": "17.0",
    "featured": "false"
}
```

### 完整配置示例

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "简短描述，编译时自动注入 deb Description 字段。",
    "homepage": "https://example.com",
    "source": "https://github.com/example/example-package",
    "developer": {
        "name": "Example Developer",
        "email": "developer@example.com"
    },
    "social": [
        {
            "name": "GitHub",
            "url": "https://github.com/example"
        }
    ],
    "section": "Tweaks",
    "architecture": "iphoneos-arm64",
    "architectures": ["iphoneos-arm64", "iphoneos-arm64e"],
    "works_min": "15.0",
    "works_max": "17.0",
    "featured": "true",
    "status": "active",
    "release_channel": "stable",
    "install_env": ["rootless", "roothide"],
    "injection": ["ellekit"],
    "install_notes": [
        "修改设置后请重启目标 App。"
    ],
    "known_conflicts": [
        "请勿与 ExampleConflict 同时安装。"
    ],
    "replaces_notice": [
        "本包替代旧版布局方案。"
    ],
    "search_keywords": ["example", "rootless", "roothide"],
    "changelog_limit": 3,
    "changelog": [
        {
            "version": "1.0.0",
            "changes": {
                "new": ["新增 rootless 支持。"],
                "improve": ["优化注入稳定性。"]
            }
        }
    ]
}
```

## 元数据字段参考

### 核心字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `bundle_id` | 是 | 包唯一标识，roothide 需以 `.roothide` 结尾 |
| `name` | 是 | 显示名称 |
| `version` | 是 | 版本号，需与 deb 内部版本一致 |
| `tagline` | 是 | 短描述，同时作为 Debian `Description` 注入 deb |
| `section` | 是 | 分类：`Tweaks` / `Roothide` / `Themes` 等 |
| `works_min` | 是 | 最低支持 iOS 版本 |
| `works_max` | 是 | 最高支持 iOS 版本 |

### 可选字段

| 字段 | 说明 |
|------|------|
| `homepage` | 项目主页链接 |
| `source` | 源代码地址 |
| `social` | 开发者社交链接 |
| `tint` | 包级独立主题色 |
| `featured` | 是否展示在精选横幅 |
| `description.md` | Markdown 长描述文件，位于 `silex_data/` 下 |

### 兼容性字段

| 字段 | 说明 |
|------|------|
| `architecture` | 架构：`iphoneos-arm64`（默认）或 `iphoneos-arm64e` |
| `architectures` | 多架构数组，如 `["iphoneos-arm64", "iphoneos-arm64e"]` |
| `install_env` | 安装环境：`rootless` / `roothide` / `rootful` |
| `injection` | 注入方式：`ellekit` 等 |

### 状态与渠道

`status` 可选值：

- `active` — 活跃维护
- `beta` — 测试阶段
- `experimental` — 实验性
- `deprecated` — 已弃用
- `internal` — 内部使用
- `archived` — 已归档

`release_channel` 可选值：

- `stable` — 稳定版
- `beta` — 测试版
- `nightly` — 每夜版
- `experimental` — 实验版

### 指引与迁移

| 字段 | 说明 |
|------|------|
| `install_notes` | 安装 / 使用注意事项 |
| `known_conflicts` | 已知冲突警告 |
| `replaces_notice` | 迁移与替代说明 |
| `search_keywords` | 额外搜索关键词 |

### 更新日志

支持纯文本和结构化两种格式。

**纯文本：**

```json
{
    "version": "1.0.0",
    "changes": "修复崩溃问题，提升启动速度。"
}
```

**结构化：**

```json
{
    "version": "1.0.0",
    "changes": {
        "new": ["新增 rootless 支持。"],
        "fix": ["修复 iOS 16 设置崩溃。"],
        "improve": ["优化注入可靠性。"],
        "remove": ["移除旧版 API。"],
        "note": ["需要重启 SpringBoard。"]
    }
}
```

使用 `changelog_limit` 控制渲染条数。

## description.md

`description.md` 是插件详情页的长描述主体，放在 `silex_data/` 下。

适用于：

- 功能概述
- 详细功能列表
- 兼容性说明
- 使用教程
- 迁移指引
- 常见问题

如果缺失，自动回退到 `tagline`。

## 首页

生成的首页是一个完整的功能门户，包含：

- 源公告横幅
- 精选插件轮播
- 分类浏览
- 包管理器一键添加按钮（Sileo / Cydia / Zebra）
- 搜索与状态/渠道/环境筛选
- 架构、注入等徽章

## 详情页

### 网页版

展示内容：横幅、图标、描述、胶囊 Tab（详情 / 更新日志）、兼容矩阵、安装说明、已知冲突、截图轮播、联系方式、开发者链接等。

网页版自带 CSS 美化，含卡片式更新日志、暗黑模式适配。

### Sileo 原生描绘

生成 Sileo 风格的 JSON 描绘，含截图轮播、Markdown 内容、元数据表格、兼容性标签、联系支持入口、更新日志 Tab 等。所有 Tab 和标签名均为中英双语。

## 编译

在项目根目录执行：

```bash
python3 index.py
```

或使用交互式脚本：

```bash
./ok.sh
```

与 `python3 index.py` 不同，`ok.sh` 会在编译前清空上次产物，确保纯净编译，并提供编译 → 发布流程。

编译成功后在 `docs/` 目录生成静态源。

## 输出产物

`docs/` 目录包含：

- `Packages`、`Packages.bz2`、`Packages.xz`、`Packages.zst`
- `Release` 及可选的 `Release.gpg`
- `pkg/` 包文件
- `depiction/web/` HTML 详情页
- `depiction/native/` Sileo 原生描绘 JSON
- `assets/` 图标、横幅、描述、截图
- `api/` JSON API 接口
- `index.html` 首页

## API 接口

所有接口均在 `docs/api/` 下以静态 JSON 形式生成。

### `api/version.json`

按 bundle_id 索引的版本信息，供插件端检测更新使用：

```json
{
  "com.example.package": {
    "version": "1.2.3",
    "date": "2026-06-11 22:45",
    "name": "Example Package"
  }
}
```

### `api/packages.json`

完整包列表，含版本、状态、渠道、环境、架构等字段。

### `api/featured.json`

精选插件列表。

### `api/search.json`

供搜索使用，含 `search_blob` 合并检索字段。

### `api/channels.json`

按发布渠道分组的包列表。

### 其他接口

- `api/tweak_release.json` — 完整元数据
- `api/repo_settings.json` — 源配置
- `api/about.json` — 编译器版本信息

## 多版本共存

本版支持同一包保留多个历史版本：

- 目录中旧版 `.deb` 不会被删除
- 最新版同时复制为 `docs/pkg/<bundle_id>.deb`（短名，Sileo 默认下载）
- 旧版本保留原始文件名
- 包索引由最新版本的元数据生成
- 用户在包管理器长按可切换版本

## 自定义

主要可定制文件在 `Styles/`：

- `index.mustache` — 首页模板
- `tweak.mustache` — 详情页模板
- `index.css` — 全局样式
- `index.js` — 首页筛选与交互逻辑
- `settings.json` — 源元数据、品牌、公告

## 快速添加新包

1. 复制 `Packages/ExamplePackage/` 为新目录
2. 替换 `silex_data/index.json`
3. 替换 `silex_data/description.md`
4. 放入 `.deb`
5. 可选添加 icon、banner、screenshots
6. 运行 `python3 index.py`

## 开源发布提示

如打算公开发布你的二开版本，建议：

- 从 `Packages/` 中移除个人包文件
- 从 `docs/` 中移除已编译产物（除非该仓库同时用作发布源）
- 替换 `Styles/settings.json` 中的示例域名和维护者信息
- 检查公告与示例链接后再发布
- 确认 `ok.sh` 中的远程仓库配置

## 许可

详见 `LICENSE` 文件。
