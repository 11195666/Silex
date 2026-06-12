# Silex

Silex 是一个面向越狱 iOS 生态的静态 APT 源生成器。

在线 Demo：[repo.mjh.im](https://repo.mjh.im) | English：[README.md](README.md)

基于 [Silica](https://github.com/Shugabuga/Silica) v1.2.2 深度二次开发，专为现代越狱环境定制。保留了原版「静态生成、无后端」的核心模型，同时补齐了 rootless / roothide 支持、多版本共存、中英双语 UI、轻量 JSON API 等关键能力。

---

## 为什么要有这个二开版

### 原始 Silica 的局限

| 局限 | 具体表现 |
|------|---------|
| 架构硬编码 `iphoneos-arm` | rootless (arm64) 和 roothide (arm64e) 均不支持 |
| 单一 deb + 重打包 | 只能保留最新版本，`dpkg-deb -b` 破坏 lzma 结构 |
| 不支持多版本共存 | 旧版 deb 直接丢弃，用户无法回退 |
| UI 全英文 | 原生描绘和网页版均无多语言支持 |
| 无版本检测接口 | 插件无法查询源上最新版本 |
| Description 依赖 Theos | 修改描述必须重新 `make package` |
| Release 架构写死 | 多架构共存时声明不准确 |
| 首页仅有包列表 | 无品牌展示、无卡片、无暗黑模式 |
| JSON ASCII 转义 | 中文在 `index.json` 中不可读 |

### 本版改造内容

#### 1. 动态架构支持

原版在 `CompileControl` 和 `CompileRelease` 中硬编码 `iphoneos-arm`。

**改造后**：`index.json` 支持 `architecture` 字段（缺省 `iphoneos-arm64`），`Release` 文件从所有包动态收集架构列表。

```json
{ "architecture": "iphoneos-arm64" }
```

生成的 `Release`：
```
Architectures: iphoneos-arm64 iphoneos-arm64e
```

文件：`util/DebianPackager.py` — `CompileControl`、`CompileRelease`

#### 2. 多版本共存

原版 `CreateDEB`：找到第一个 .deb → 重命名为 `bundle_id.deb` → return，其余版本全部丢失。

**改造后**：遍历所有 .deb → 按版本降序排列 → 旧版本保留原始文件名 → 最新版同时复制为 `bundle_id.deb`（短名用作下载链接）。

```
docs/pkg/
├── im.mjh.fakeperm.deb                       ← 最新版，短名下载
├── im.mjh.fakeperm_8.3.0_iphoneos-arm64.deb  ← 历史版本
└── im.mjh.fakeperm_8.5.0_iphoneos-arm64.deb  ← 历史版本
```

`dpkg-scanpackages -m` 原生支持同 Package 名下多条版本记录。Sileo/Cydia 长按包名即可切换版本。

文件：`util/DebianPackager.py` — `CreateDEB`

#### 3. 直接复制原始 deb（不再重打包）

原版用 `dpkg-deb -b` 重打包（破坏 lzma tar），导致 roothide dpkg 报 "Read-only file system"。

**改造后**：直接复制 Theos 生成的原始 .deb，保留原始压缩格式和属性结构。

文件：`util/DebianPackager.py` — `CreateDEB`

#### 4. Roothide 支持

roothide 与 rootless 共享同一 Theos 编译产物，仅架构不同（arm64e vs arm64）。原版无法处理双重 bundle_id。

**改造后**：
- 独立 Package 目录 `虚拟权限_Roothide/` → `bundle_id: im.mjh.fakeperm.roothide`
- 编译时自动修改 deb 内部控制字段（`Package: im.mjh.fakeperm` → `im.mjh.fakeperm.roothide`）
- 自动注入 `Name: ... (Roothide)`
- 自动将 `Section` 改为 `Roothide`（独立分类展示）

新增函数：`PatchDebControl(deb_path, replacements)` —— 用 ar/zstd/tar 系统工具修改控制字段，不重打包。

文件：`util/DebianPackager.py` — `PatchDebControl`

#### 5. tagline 自动注入 Description

原版：Description 完全依赖 Theos 编译时注入的 control 文件。

**改造后**：编译时自动从 `index.json` 的 `tagline` 注入所有 deb 的 `Description` 字段。修改描述只需改 tagline + 重新编译。

文件：`util/DebianPackager.py` — `CreateDEB`

#### 6. 版本检测接口

新增 `GET /api/version.json`

```json
{
  "im.mjh.fakeperm": {
    "version": "8.6.0",
    "date": "2026-06-11 22:45",
    "name": "虚拟权限 · Fake Permission"
  }
}
```

插件端实现逻辑：
1. `GET` 完整 JSON → 按 `MY_BUNDLE_ID` 取值
2. 比较 `version > 本地版本` → 显示红色 Badge "vX.Y.Z 可用"
3. 否则不显示

文件：`util/DepictionGenerator.py` — `RenderVersionAPI`

#### 7. 个人名片式首页

原版：包列表 + 外部 index.css。

**改造后**：独立卡片式首页（不引用外部 CSS），含头像、源名、描述、三个包管理器一键添加按钮，支持暗黑模式。

| 按钮 | URL Scheme |
|------|-----------|
| Sileo | `sileo://source/https://` |
| Cydia | `cydia://url/https://…` |
| Zebra | `zbra://sources/add/https://` |

文件：`Styles/index.mustache`

#### 8. 中英双语详情页

原版：全英文（Details / Changelog / Information / Developer 等）。

**改造后**：
- 导航：`详情 Details` / `更新日志 Changelog`
- 信息表：`开发者 Developer` / `版本 Version` / `兼容性 Compatibility` / `分类 Section`
- Roothide section 自动在名称后追加 `(Roothide)` 标识
- 兼容性 JS 提示也改为中英双语

文件：`Styles/tweak.mustache`、`Styles/index.js`、`util/DepictionGenerator.py` — `RenderPackageHTML`

#### 9. Sileo 原生描绘中英双语

所有 JSON 原生描绘的标签和 Tab 名均为中英双语。

文件：`util/DepictionGenerator.py` — `RenderPackageNative`、`RenderNativeChangelog`

#### 10. copytree 防碰撞

`shutil.copytree` 增加 `dirs_exist_ok=True`，防止残留 temp/ 导致 `FileExistsError`。

文件：`index.py` Step 6

#### 11. 编译前自动清理

`ok.sh`：每次编译前清空上次所有产物，确保干净编译。

#### 12. 交互式编译发布脚本

`ok.sh` 流程：
```
是否编译? (y/n): y
→ 编译中
编译完成！
是否发布推送? (y/n): y
请输入 commit 信息: ...
→ 自动 git add/commit/push
```

#### 13. index.json 中文可读

`json.dump` 使用 `ensure_ascii=False, indent=4`，JSON 文件中中文可读、可手动编辑。

文件：`util/DebianPackager.py`

### 与上游对比

| 特性 | 上游 Silica | Silex |
|------|-----------|------|
| 架构支持 | 仅 `iphoneos-arm` | arm64 / arm64e 动态收集 |
| 多版本共存 | 不支持 | 自动按版本排序归档 |
| deb 处理 | `dpkg-deb` 重打包 | 直接复制原包 + 按需注入字段 |
| Roothide | 不支持 | 独立分类 + 自动改名 |
| tagline → Description | 必须改 Theos | 改 index.json 即生效 |
| 版本检测接口 | 无 | `/api/version.json` |
| 首页 | 包列表 | 个人名片式（一键添加） |
| 详情页 UI | 英文 | 中英双语 |
| 编译脚本 | `setup.sh` | `ok.sh`（交互式编译+发布） |
| JSON 可读性 | ASCII 转义 | 中文可读 |

---

## 截图

| 首页 | 插件详情 |
|------|---------|
| ![首页](screenshots/homepage.png) | ![详情](screenshots/depiction.png) |

| Sileo 原生描绘 | 更新日志 |
|------|---------|
| ![原生](screenshots/native.png) | ![更新日志](screenshots/changelog.png) |

> 截图放至 `screenshots/` 目录即可。

---

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

```text
Packages/
├── 虚拟权限/                  # rootless 版本 (arm64)
│   ├── xxx_8.3.0_iphoneos-arm64.deb
│   ├── xxx_8.5.0_iphoneos-arm64.deb  ← 多版本共存
│   └── silex_data/
│       ├── index.json
│       ├── description.md
│       ├── icon.png
│       ├── banner.png
│       ├── screenshots/
│       └── scripts/
│
├── 虚拟权限_Roothide/          # roothide 版本 (arm64e)
│   ├── xxx_8.6.0_iphoneos-arm64e.deb
│   └── silex_data/
│       ├── index.json          # bundle_id: xxx.roothide
│       └── …
```

注意事项：
- 同一包的 arm64 和 arm64e 版本需分目录存放
- Roothide 的 `bundle_id` 需以 `.roothide` 结尾
- macOS `ar` 产生的 `._` 资源叉文件已被 `PatchDebControl` 自动过滤
- `dpkg-scanpackages` 的 "uninitialized value" 警告无影响（dpkg 的 bug）

---

## 环境要求

### 系统依赖

macOS：

```bash
brew install dpkg zstd
```

Debian / Ubuntu：

```bash
sudo apt-get install dpkg-dev gnupg git xz-utils bzip2 zstd
```

### Python

- Python 3+
- `pip`

```bash
pip install -r requirements.txt
```

---

## 源配置

主配置位于 `Styles/settings.json`：

```json
{
    "name": "Silex",
    "description": "A customizable static repository generated with Silex.",
    "tint": "#27BEF5",
    "cname": "repo.example.com",
    "maintainer": { "name": "Repo Maintainer", "email": "maintainer@example.com" },
    "social": [{ "name": "Project Homepage", "url": "https://example.com" }],
    "announcements": [{ "level": "warning", "title": "提示", "message": "在此添加源公告内容。" }],
    "automatic_git": "false",
    "footer": "{{repo_name}} · Updated {{silex_compile_date}}",
    "enable_gpg": "false"
}
```

| 字段 | 说明 |
|------|------|
| `name` | 源显示名称 |
| `description` | 源简介 |
| `tint` | 默认主题色（Hex） |
| `cname` | 公开域名，不含 `https://` |
| `maintainer` | 源维护者 |
| `social` | 源级社交链接，在支持页面展示 |
| `announcements` | 首页公告横幅 |
| `automatic_git` | 编译后自动 git 提交 |
| `enable_gpg` | 签名 `Release.gpg` |
| `footer` | Mustache 模板渲染的页脚 |

公告级别：`info`、`warning`、`error`、`success`。

---

## 包元数据 (index.json)

### 最小配置

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "简短描述文本。",
    "developer": { "name": "Example Developer" },
    "section": "Tweaks",
    "architecture": "iphoneos-arm64",
    "works_min": "15.0",
    "works_max": "17.0",
    "featured": "false"
}
```

### 完整配置

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "简短描述，编译时自动注入 deb Description 字段。",
    "homepage": "https://example.com",
    "source": "https://github.com/example/example-package",
    "developer": { "name": "Example Developer", "email": "developer@example.com" },
    "social": [{ "name": "GitHub", "url": "https://github.com/example" }],
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
    "install_notes": ["修改设置后请重启目标 App。"],
    "known_conflicts": ["请勿与 ExampleConflict 同时安装。"],
    "replaces_notice": ["本包替代旧版布局方案。"],
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
| `version` | 是 | 版本号，需与 deb 内部控制版本一致 |
| `tagline` | 是 | 短描述，编译时注入 deb `Description` 字段 |
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
| `description.md` | Markdown 长描述，位于 `silex_data/` 下 |

### 状态与渠道

`status`：`active`（活跃）、`beta`（测试）、`experimental`（实验）、`deprecated`（弃用）、`internal`（内部）、`archived`（归档）

`release_channel`：`stable`（稳定）、`beta`（测试）、`nightly`（每夜）、`experimental`（实验）

### 更新日志

纯文本：

```json
{ "version": "1.0.0", "changes": "修复崩溃问题，提升启动速度。" }
```

结构化：

```json
{ "version": "1.0.0", "changes": {
    "new": ["新增 rootless 支持。"],
    "fix": ["修复 iOS 16 设置崩溃。"],
    "improve": ["优化注入可靠性。"],
    "remove": ["移除旧版 API。"],
    "note": ["需要重启 SpringBoard。"]
}}
```

使用 `changelog_limit` 控制渲染条数。

---

## description.md

`description.md` 是插件详情页的长描述主体（Markdown 格式），放在 `silex_data/` 下。

适用于：功能概述、详细特性、兼容性说明、使用教程、迁移指引、常见问题。

如果缺失，自动回退到 `tagline`。

---

## 首页

生成的首页是一个完整的功能门户：

- 源公告横幅
- 精选插件轮播
- 分类浏览
- 一键添加按钮（Sileo / Cydia / Zebra）
- 搜索 + 状态/渠道/环境筛选
- 架构、注入等徽章
- 暗黑模式

## 详情页

### 网页版

横幅、图标、胶囊 Tab（详情 / 更新日志）、Markdown 描述、兼容矩阵、安装说明、已知冲突、截图轮播、社交链接、暗黑模式。CSS 完全自定义，卡片式更新日志。

### Sileo 原生描绘

生成 Sileo JSON 格式描绘，含截图轮播、Markdown 内容、元数据表格、兼容性标签、联系支持入口、更新日志 Tab。所有 Tab 和标签均为中英双语。

---

## 编译

```bash
python3 index.py
```

或使用交互式脚本：

```bash
./ok.sh
```

与 `python3 index.py` 不同，`ok.sh` 会在编译前清空上次产物，确保纯净编译，并提供编译 → 发布完整流程。

编译产物在 `docs/` 目录。

## 输出产物

- `Packages`、`Packages.bz2`、`Packages.xz`、`Packages.zst`
- `Release`（及可选 `Release.gpg`）
- `pkg/` — 包文件
- `depiction/web/` — HTML 详情页
- `depiction/native/` — Sileo 原生描绘 JSON
- `assets/` — 图标、横幅、描述、截图
- `api/` — JSON API 接口
- `index.html` — 首页

---

## API 接口

全部为 `docs/api/` 下的静态 JSON。

### `api/version.json`

按 bundle_id 索引的版本信息，供插件端检测更新：

```json
{ "com.example.package": { "version": "1.2.3", "date": "2026-06-11 22:45", "name": "Example Package" } }
```

### `api/packages.json`

完整包列表，含版本、状态、渠道、环境、架构、开发者、摘要。

### `api/featured.json`

精选插件列表，含摘要和状态/渠道标签。

### `api/search.json`

供搜索使用，含 `search_blob` 合并检索字段。

### `api/channels.json`

按发布渠道分组的包列表。

### 其他接口

- `api/tweak_release.json` — 完整元数据
- `api/repo_settings.json` — 源配置
- `api/about.json` — 编译器版本信息

---

## 多版本共存

- 目录中旧版 `.deb` 不会被删除
- 最新版同时复制为 `docs/pkg/<bundle_id>.deb`（短名，默认下载）
- 旧版本保留原始文件名
- 包索引使用最新版本元数据
- 用户在包管理器长按可切换版本

---

## 自定义

主要可定制文件在 `Styles/`：

- `index.mustache` — 首页模板
- `tweak.mustache` — 详情页模板
- `index.css` — 全局样式
- `index.js` — 首页筛选与交互逻辑
- `settings.json` — 源元数据、品牌、公告

---

## 快速添加新包

1. 复制 `Packages/ExamplePackage/` 为新目录
2. 替换 `silex_data/index.json`
3. 替换 `silex_data/description.md`
4. 放入 `.deb`
5. 可选添加 icon、banner、screenshots
6. 运行 `python3 index.py`

---

## 开源发布提示

如打算公开发布你的二开版本，建议：

- 从 `Packages/` 移除个人包文件
- 从 `docs/` 移除已编译产物（除非该仓库同时用作发布源）
- 替换 `Styles/settings.json` 中的示例域名和维护者信息
- 检查公告与示例链接后再发布
- 确认 `ok.sh` 中远程仓库配置正确

---

## 许可

详见 `LICENSE` 文件。
