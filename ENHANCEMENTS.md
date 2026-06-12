# Silex

基于 [Shuga/Silica](https://github.com/Shugabuga/Silica) v1.2.2 二次开发（项目名 **Silex**），针对现代越狱生态环境的深度定制版本。

## 一、原始 Silica 的局限

| 局限 | 具体表现 |
|------|---------|
| 架构固定 `iphoneos-arm` | rootless (arm64) 和 roothide (arm64e) 均不支持 |
| 单一 deb + 重打包 | 只能保留最新版本，不支持多版本共存 |
| dpkg-deb 重建破坏 lzma 结构 | Theos 生成的标准 deb 被重新打包后，roothide dpkg 报 Read-only file system |
| Sileo 原生 depiction 全英文 | 不支持多语言 UI |
| 无版本检测接口 | 插件无法查询源上最新版本 |
| Description 依赖 Theos control | 修改描述必须重新 make package |
| Release 架构写死 | 多架构共存时 Release 声明不准确 |
| 首页原始布局 | 包列表式首页，无个性化 |
| 无合成图片/排版支持 | 不生成 screenshots 等 |
| Windows/Linux 工具链依赖 | deb 操作依赖 dpkg-deb（Windows 用户必需 WSL） |

---

## 二、本版改造内容

### 核心架构改造

#### 1. 动态架构支持

原版在 `CompileControl` 里硬编码 `Architecture: iphoneos-arm`，`CompileRelease` 里硬编码 `Architectures: iphoneos-arm`。

**改造后**：`index.json` 支持 `"architecture"` 字段（缺省 `iphoneos-arm64`）。`Release` 文件自动从所有包收集架构列表。

文件：`util/DebianPackager.py` CompileControl、CompileRelease

```json
// index.json
{
    "architecture": "iphoneos-arm64"    // 可选，缺省 iphoneos-arm64
}
```

生成的 Release：
```
Architectures: iphoneos-arm64 iphoneos-arm64e
```

#### 2. 多版本共存

原版 `CreateDEB`：找到第一个 .deb → 重命名为 `bundle_id.deb` → return，其他版本全部丢失。

**改造后**：遍历所有 .deb → 按版本降序排列 → 旧版本保留原始文件名 → 最新版本同时复制为 `bundle_id.deb`（短名用作下载链接）。

```
docs/pkg/
├── im.mjh.fakeperm.deb                    ← 最新版短名（下载链接用）
├── im.mjh.fakeperm_8.3.0_iphoneos-arm64.deb  ← 历史版本
└── im.mjh.fakeperm_8.5.0_iphoneos-arm64.deb  ← 历史版本
```

`dpkg-scanpackages -m` 原生支持同 Package 名下多条版本记录，Sileo/Cydia 长按包名选择历史版本。

文件：`util/DebianPackager.py` CreateDEB

#### 3. 直接复制原始 deb（不再重打包）

原版 `CreateDEB` 用 `dpkg-deb -b` 重新打包（destroys lzma tar），导致 roothide dpkg 报 "Read-only file system"。

**改造后**：直接复制 Theos 生成的原始 .deb，保留原始压缩格式和属性结构。

文件：`util/DebianPackager.py` CreateDEB

#### 4. Roothide 支持

roothide 与 rootless 共享同一 Theos 编译产物，仅架构不同（arm64e vs arm64）。原版无法支持双重 bundle_id。

**改造后**：
- 独立Package目录 `虚拟权限_Roothide/` → `bundle_id: im.mjh.fakeperm.roothide`
- 编译时自动将 deb 内部控制文件中的 `Package: im.mjh.fakeperm` 修改为 `im.mjh.fakeperm.roothide`
- 自动追加 `Name: 虚拟权限 · Fake Permission (Roothide)`
- 自动将 `Section` 修改为 `Roothide`（Roothide 分类独立展示）

新增函数：`PatchDebControl(deb_path, replacements)`——用 ar/zstd/tar 系统工具解析并修改控制字段。

文件：`util/DebianPackager.py` PatchDebControl

#### 5. tagline 自动注入 Description

原版：Description 完全依赖 Theos 编译时注入的 control 文件。

**改造后**：编译时自动从 `index.json` 的 `tagline` 注入所有 deb 的 `Description` 字段。修改描述只需改 tagline + 重新编译。

文件：`util/DebianPackager.py` CreateDEB 注入逻辑

---

### 接口层新增

#### 6. 版本检测接口

新增 `GET /api/version.json`

```json
{
  "im.mjh.fakeperm": {
    "version": "8.6.0",
    "date": "2026-06-11 22:45",
    "name": "虚拟权限 · Fake Permission"
  },
  ...
}
```

插件端实现逻辑：
```
1. GET 完整 JSON → 按 MY_BUNDLE_ID 取值
2. 比较 version > 本地版本 → 显示红色 Badge "vX.Y.Z 可用"
3. 否则不显示
```

文件：`util/DepictionGenerator.py` RenderVersionAPI

---

### UI 层改造

#### 7. 首页：个人名片式

原版：包列表 + public index.css 引用。

**改造后**：独立卡片式首页（不引用任何外部 CSS），含头像、源名、描述、三个包管理器一键添加按钮，支持暗黑模式。

| 按钮 | URL Scheme |
|------|-----------|
| Sileo | `sileo://source/https://` |
| Cydia | `cydia://url/https://...` |
| Zebra | `zbra://sources/add/https://` |

文件：`Styles/index.mustache`

#### 8. 详情页：中英双语

原版：全部英文（Details / Changelog / Information / Developer 等）。兼容性信息也是 "This package is compatible with..."。

**改造后**：
- 导航：`详情 Details` / `更新日志 Changelog`
- 信息表：`开发者 Developer` / `版本 Version` / `兼容性 Compatibility` / `分类 Section`
- Roothide section 自动在名称后追加 `(Roothide)` 标识
- 兼容性 JS 提示也改为中英双语

文件：`Styles/tweak.mustache`、`Styles/index.js`、`util/DepictionGenerator.py` RenderPackageHTML

#### 9. Sileo 原生 depiction 中英双语

Sileo 显示的 JSON depiction 标签全部改为中英双语。

文件：`util/DepictionGenerator.py` RenderPackageNative、RenderNativeChangelog

---

### 稳定性加固

#### 10. copytree 防碰撞

`shutil.copytree` 增加 `dirs_exist_ok=True`，防止残留 temp/ 导致 `FileExistsError`。

文件：`index.py` Step 6

#### 11. 编译前自动清理

`ok.sh`（原 compile.sh）：编译前自动删除所有上次产物，确保干净编译。

#### 12. 交互式发布脚本

`ok.sh` 交互流程：
```
是否编译? (y/n): y
→ 编译
编译完成！
是否发布推送? (y/n): y
请输入 commit 信息: xxx
→ 自动 git add/commit/push（代理自动追加）
```

#### 13. 操作脚本保护

`json.dump` 使用 `ensure_ascii=False, indent=4`，JSON 文件中中文可读、可手动编辑。

文件：`util/DebianPackager.py`

---

## 三、与上游对比

| 特性 | 上游 Silica | 本版 |
|------|-----------|------|
| 架构支持 | iphoneos-arm | arm64 / arm64e 动态收集 |
| 多版本共存 | 不支持 | 自动按版本排序归档 |
| deb 处理 | dpkg-deb 重打包 | 直接复制原包 + 按需注入字段 |
| roothide 支持 | 不支持 | 独立 section + 自动改名 |
| tagline→Description | 必须改 Theos | 改 index.json 即生效 |
| 版本检测接口 | 无 | /api/version.json |
| 首页 | 包列表 | 个人名片式（一键添加） |
| 详情页 | 英文 | 中英双语 |
| Sileo depiction | 英文 | 中英双语 |
| 脚本 | setup.sh | ok.sh（编译+发布引导） |
| index.json 可读性 | ASCII 转义 | 中文可读 |

---

## 四、快速开始

```bash
# 1. 安装依赖
brew install dpkg zstd  # macOS

# 2. 配置源信息
# 编辑 Styles/settings.json

# 3. 放包
# 将 .deb 放入 Packages/<包名>/
# 编辑 Packages/<包名>/silex_data/index.json

# 4. 编译
./ok.sh
```

### 包目录结构

```
Packages/
├── 虚拟权限/                  # 普通包 (rootless arm64)
│   ├── xxx_8.3.0_iphoneos-arm64.deb
│   ├── xxx_8.5.0_iphoneos-arm64.deb  ← 多版本共存
│   └── silex_data/
│       ├── index.json
│       ├── icon.png
│       ├── banner.png
│       └── description.md      # 可选，Web 详情页用
│
├── 虚拟权限_Roothide/          # roothide 分支 (arm64e)
│   ├── xxx_8.6.0_iphoneos-arm64e.deb
│   └── silex_data/
│       ├── index.json          # bundle_id: xxx.roothide
│       └── ...（素材同主包）
│
└── 其他包...
```

### index.json 关键字段

```json
{
    "bundle_id": "im.mjh.fakeperm",
    "name": "虚拟权限 · Fake Permission",
    "version": "8.6.0",
    "tagline": "描述文本，编译时注入 Description",
    "section": "Tweaks",
    "architecture": "iphoneos-arm64",
    "works_min": "15.0",
    "works_max": "17.0",
    "featured": "true",
    "changelog": [...]
}
```

| 字段 | 必需 | 说明 |
|------|------|------|
| `bundle_id` | 是 | 包唯一标识，roothide 需加 `.roothide` 后缀 |
| `name` | 是 | 显示名称，roothide 自动追加 (Roothide) |
| `version` | 是 | 版本号，与 deb 内部控制文件一致 |
| `tagline` | 是 | 短描述，编译时注入 deb Description 字段 |
| `section` | 是 | 分类：Tweaks / Roothide / Themes 等 |
| `architecture` | 否 | iphoneos-arm64（默认）或 iphoneos-arm64e |
| `works_min/max` | 是 | iOS 兼容范围 |
| `featured` | 否 | 是否在 Sileo 精选横幅展示 |
| `changelog` | 否 | 更新日志列表 |

## 五、注意事项

- roothide 目录必须独立，`bundle_id` 需以 `.roothide` 结尾
- arm64 和 arm64e 不能混放同一目录（会被映射到不同 bundle_id）
- macOS `ar` 会产生 `._` 资源叉文件，`PatchDebControl` 已自动过滤
- `tagline` 中的空行用 `\n\n`，自动转换为 dpkg 的 ` .` 段落分隔符
- `dpkg-scanpackages` 的 "uninitialized value" 警告无影响，是 dpkg 的 bug

## 六、协议

基于 [Silica](https://github.com/Shugabuga/Silica) 二次开发，沿用原始协议。
