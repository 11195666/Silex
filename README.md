# Silex

Silex is a static APT repository generator for jailbroken iOS package feeds.

在线 Demo：[repo.mjh.im](https://repo.mjh.im) | 中文文档：[README_zh.md](README_zh.md)

Forked from [Silica](https://github.com/Shugabuga/Silica) v1.2.2, Silex is a deep customisation for the modern jailbreak ecosystem. It keeps the original "static generation, no backend" model while adding rootless/roothide support, multi-version packages, bilingual UI, lightweight JSON APIs, and more.

---

## Why this fork exists

### Original Silica limitations

| Limitation | Detail |
|------|---------|
| Hardcoded `iphoneos-arm` | No rootless (arm64) or roothide (arm64e) support |
| Single deb + repack | Only one version per package; `dpkg-deb -b` breaks lzma archives |
| No multi-version | Older debs discarded — users can't roll back |
| English-only UI | Native depictions and web pages have no i18n support |
| No version-check API | Packages can't query the repo for updates |
| Description tied to Theos | Modifying descriptions requires `make package` |
| Hardcoded Release architectures | Inaccurate when multiple architectures coexist |
| Bare package-list homepage | No branding, no cards, no dark mode |
| ASCII-escaped JSON | Chinese text unreadable in `index.json` |

### What this fork changes

#### 1. Dynamic architecture support

Upstream hardcoded `iphoneos-arm` in `CompileControl` and `CompileRelease`.

**After**: `index.json` supports an `architecture` field (defaults to `iphoneos-arm64`). The `Release` file collects architectures dynamically from all packages.

```json
{ "architecture": "iphoneos-arm64" }
```

Generated `Release`:
```
Architectures: iphoneos-arm64 iphoneos-arm64e
```

Files: `util/DebianPackager.py` — `CompileControl`, `CompileRelease`

#### 2. Multi-version coexistence

Upstream `CreateDEB`: found the first `.deb` → renamed to `bundle_id.deb` → returned. All other versions were discarded.

**After**: iterates all `.deb` files → sorts by version descending → keeps older versions with their original filenames → copies the latest also as `bundle_id.deb` (short name for the download link).

```
docs/pkg/
├── im.mjh.fakeperm.deb                       ← latest, short-name download
├── im.mjh.fakeperm_8.3.0_iphoneos-arm64.deb  ← historical version
└── im.mjh.fakeperm_8.5.0_iphoneos-arm64.deb  ← historical version
```

`dpkg-scanpackages -m` natively supports multiple entries for the same Package name. In Sileo/Cydia, long-press a package to switch versions.

File: `util/DebianPackager.py` — `CreateDEB`

#### 3. Direct copy (no repack)

Upstream `CreateDEB` used `dpkg-deb -b` to repack, destroying the original lzma tar and causing roothide's dpkg to error with "Read-only file system".

**After**: directly copies the Theos-produced original `.deb`, preserving the original compression format and structure.

File: `util/DebianPackager.py` — `CreateDEB`

#### 4. Roothide support

roothide packages share the same Theos output as rootless, differing only in architecture (arm64e vs arm64). Upstream couldn't handle dual bundle_ids.

**After**:
- Separate package directory (`虚拟权限_Roothide/` → `bundle_id: im.mjh.fakeperm.roothide`)
- At compile time: patches the deb's internal control file (`Package: im.mjh.fakeperm` → `im.mjh.fakeperm.roothide`)
- Auto-injects `Name: ... (Roothide)`
- Auto-sets `Section: Roothide` for independent category display

New function: `PatchDebControl(deb_path, replacements)` — uses ar/zstd/tar to modify control fields without repacking.

File: `util/DebianPackager.py` — `PatchDebControl`

#### 5. Tagline → Description injection

Upstream: Description depended entirely on the control file from Theos.

**After**: auto-injects `index.json`'s `tagline` into every deb's `Description` field at compile time. To update a description, just edit the tagline and recompile.

File: `util/DebianPackager.py` — `CreateDEB`

#### 6. Version-check API

New endpoint: `GET /api/version.json`

```json
{
  "im.mjh.fakeperm": {
    "version": "8.6.0",
    "date": "2026-06-11 22:45",
    "name": "Fake Permission"
  }
}
```

Client logic:
1. `GET` the full JSON → lookup by `MY_BUNDLE_ID`
2. If `version > local_version` → show a red badge "vX.Y.Z available"
3. Otherwise do nothing

File: `util/DepictionGenerator.py` — `RenderVersionAPI`

#### 7. Personal-card homepage

Upstream: a package list + external `index.css`.

**After**: standalone card-style homepage (no external CSS), with avatar, repo name, description, three one-tap add-to-package-manager buttons, and dark mode.

| Button | URL Scheme |
|------|-----------|
| Sileo | `sileo://source/https://` |
| Cydia | `cydia://url/https://…` |
| Zebra | `zbra://sources/add/https://` |

File: `Styles/index.mustache`

#### 8. Bilingual depiction UI

Upstream: English-only (Details / Changelog / Information / Developer, etc.).

**After**:
- Nav tabs: `Details / 更新日志 Changelog`
- Info table: `Developer / Version / Compatibility / Section` (all bilingual)
- Roothide section auto-appends `(Roothide)` to package name
- JS compatibility hints also bilingual

Files: `Styles/tweak.mustache`, `Styles/index.js`, `util/DepictionGenerator.py` — `RenderPackageHTML`

#### 9. Bilingual Sileo native depictions

All JSON native depiction labels and tab names are now bilingual.

File: `util/DepictionGenerator.py` — `RenderPackageNative`, `RenderNativeChangelog`

#### 10. copytree collision prevention

`shutil.copytree` now uses `dirs_exist_ok=True` to prevent `FileExistsError` from stale `temp/` directories.

File: `index.py` Step 6

#### 11. Automatic pre-build cleanup

`ok.sh`: clears all previous outputs before each build to ensure a clean compile.

#### 12. Interactive build/push script

`ok.sh` workflow:
```
Compile? (y/n): y
→ compiling
Done!
Publish & push? (y/n): y
Enter commit message: ...
→ automatic git add/commit/push
```

#### 13. Human-readable index.json

`json.dump` uses `ensure_ascii=False, indent=4` so Chinese text in JSON files is readable and manually editable.

File: `util/DebianPackager.py`

### Comparison table

| Feature | Upstream Silica | Silex |
|------|-----------|------|
| Architecture | `iphoneos-arm` only | arm64 / arm64e, dynamic collection |
| Multi-version | No | Auto-sorted by version, archived |
| Deb handling | `dpkg-deb` repack | Direct copy + field patching |
| Roothide | Not supported | Independent section + auto-rename |
| Tagline → Description | Must modify Theos | Edit `index.json` → recompile |
| Version-check API | None | `/api/version.json` |
| Homepage | Package list | Personal card (one-tap add) |
| Depiction UI | English only | Bilingual (zh + en) |
| Build script | `setup.sh` | `ok.sh` (interactive build + push) |
| JSON readability | ASCII-escaped | Human-readable Chinese |

---

## Screenshots

| Homepage | Package Detail |
|------|---------|
| ![Homepage](screenshots/homepage.png) | ![Detail](screenshots/depiction.png) |

| Sileo Native | Changelog |
|------|---------|
| ![Native](screenshots/native.png) | ![Changelog](screenshots/changelog.png) |

> Place screenshots in the `screenshots/` directory.

---

## Project Structure

```text
Silex/
├── index.py                  # Main compiler entry
├── Packages/                 # Package directory (debs + metadata)
├── Styles/                   # Templates and branding assets
├── util/                     # Compiler helpers
├── docs/                     # Generated static repo output
├── ok.sh                     # Interactive build/push script
└── requirements.txt          # Python dependencies
```

## Package Layout

```text
Packages/
├── MyTweak/                  # rootless (arm64)
│   ├── mytweak_1.0.0_iphoneos-arm64.deb
│   ├── mytweak_1.1.0_iphoneos-arm64.deb  ← multiple versions
│   └── silex_data/
│       ├── index.json
│       ├── description.md
│       ├── icon.png
│       ├── banner.png
│       ├── screenshots/
│       └── scripts/
│
├── MyTweak_Roothide/         # roothide branch (arm64e)
│   ├── mytweak_1.1.0_iphoneos-arm64e.deb
│   └── silex_data/
│       ├── index.json        # bundle_id: xxx.roothide
│       └── …
```

Notes:
- arm64 and arm64e versions of the same package must live in separate directories
- Roothide `bundle_id` must end with `.roothide`
- On macOS, `._` resource-fork files from `ar` are auto-filtered by `PatchDebControl`
- `dpkg-scanpackages` "uninitialized value" warnings are cosmetic (dpkg bug)

## Requirements

### System

macOS:

```bash
brew install dpkg zstd
```

Debian / Ubuntu:

```bash
sudo apt-get install dpkg-dev gnupg git xz-utils bzip2 zstd
```

### Python

- Python 3+
- `pip`

```bash
pip install -r requirements.txt
```

## Configuration

Main repo config at `Styles/settings.json`:

```json
{
    "name": "Silex",
    "description": "A customizable static repository generated with Silex.",
    "tint": "#27BEF5",
    "cname": "repo.example.com",
    "maintainer": { "name": "Repo Maintainer", "email": "maintainer@example.com" },
    "social": [{ "name": "Project Homepage", "url": "https://example.com" }],
    "announcements": [{ "level": "warning", "title": "Notice", "message": "Add your message here." }],
    "automatic_git": "false",
    "footer": "{{repo_name}} · Updated {{silex_compile_date}}",
    "enable_gpg": "false"
}
```

| Field | Description |
|------|-------------|
| `name` | Repo display name |
| `description` | Short repo description |
| `tint` | Default accent colour (hex) |
| `cname` | Public domain, without `https://` |
| `maintainer` | Repo maintainer info |
| `social` | Repo-level links shown in support views |
| `announcements` | Homepage banner notices |
| `automatic_git` | Auto git commit after compile |
| `enable_gpg` | Sign `Release.gpg` |
| `footer` | Mustache-rendered footer |

Announcement levels: `info`, `warning`, `error`, `success`.

---

## Package Metadata (`index.json`)

### Minimal example

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "A short description.",
    "developer": { "name": "Example Developer" },
    "section": "Tweaks",
    "architecture": "iphoneos-arm64",
    "works_min": "15.0",
    "works_max": "17.0",
    "featured": "false"
}
```

### Full example

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "Short summary — auto-injected as deb Description.",
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
    "install_notes": ["Restart the target app after changing settings."],
    "known_conflicts": ["Do not install alongside ExampleConflict."],
    "replaces_notice": ["This package replaces the older legacy layout."],
    "search_keywords": ["example", "rootless", "roothide"],
    "changelog_limit": 3,
    "changelog": [
        {
            "version": "1.0.0",
            "changes": {
                "new": ["Added rootless support."],
                "improve": ["Improved injection reliability."]
            }
        }
    ]
}
```

## Metadata field reference

### Core fields

| Field | Required | Description |
|------|----------|-------------|
| `bundle_id` | Yes | Unique package ID; `.roothide` suffix for roothide |
| `name` | Yes | Display name |
| `version` | Yes | Must match the deb's internal version |
| `tagline` | Yes | Short description; injected as deb `Description` |
| `section` | Yes | Category: `Tweaks`, `Roothide`, `Themes`, etc. |
| `works_min` | Yes | Minimum iOS version |
| `works_max` | Yes | Maximum iOS version |

### Optional fields

| Field | Description |
|------|-------------|
| `homepage` | Project homepage URL |
| `source` | Source code URL |
| `social` | Developer social links |
| `tint` | Package-specific accent colour |
| `featured` | Show in featured carousel |
| `description.md` | Markdown long description (in `silex_data/`) |

### Status & channel

`status`: `active`, `beta`, `experimental`, `deprecated`, `internal`, `archived`

`release_channel`: `stable`, `beta`, `nightly`, `experimental`

### Changelog

Plain text:

```json
{ "version": "1.0.0", "changes": "Fixed crashes and improved startup speed." }
```

Structured:

```json
{ "version": "1.0.0", "changes": {
    "new": ["Added rootless support."],
    "fix": ["Fixed settings crash on iOS 16."],
    "improve": ["Improved injection reliability."],
    "remove": ["Removed legacy API."],
    "note": ["Requires SpringBoard restart."]
}}
```

Use `changelog_limit` to cap the number of rendered entries.

---

## Description files & assets

### `description.md`

The main long-form depiction body. Supports full Markdown. If missing, falls back to `tagline`.

### Optional assets

- `icon.png` — package icon
- `banner.png` — package banner
- `screenshots/` — screenshot carousel images
- `scripts/` — maintainer scripts copied into `DEBIAN/`

---

## Homepage

The generated homepage is a full-featured package portal:

- Repo announcement banners
- Featured package carousel
- Section-based browsing
- One-tap add buttons (Sileo / Cydia / Zebra)
- Search + filter by status, channel, environment
- Architecture and injection badges
- Dark mode

## Depictions

### Web depictions

Banner, icon, capsule tabs (Details / Changelog), Markdown description, compatibility matrix, install notes, known conflicts, screenshot carousel, social links, dark mode — all with custom CSS.

### Native depictions

Sileo-formatted JSON depictions with screenshots, Markdown content, metadata tables, compatibility labels, support actions, and a changelog tab. All tab and label names are bilingual.

---

## Build

```bash
python3 index.py
```

Or use the interactive script:

```bash
./ok.sh
```

Unlike `python3 index.py`, `ok.sh` clears previous outputs first for a clean build, and walks you through compile → commit → push.

Output goes to `docs/`.

## Output

- `Packages`, `Packages.bz2`, `Packages.xz`, `Packages.zst`
- `Release` (and optional `Release.gpg`)
- `pkg/` — package files
- `depiction/web/` — HTML depictions
- `depiction/native/` — native depiction JSON
- `assets/` — icons, banners, descriptions, screenshots
- `api/` — JSON API endpoints
- `index.html` — homepage

---

## API Endpoints

All are static JSON files under `docs/api/`.

### `api/version.json`

Version lookup keyed by bundle ID:

```json
{ "com.example.package": { "version": "1.2.3", "date": "2026-06-11 22:45", "name": "Example Package" } }
```

### `api/packages.json`

Full package list with version, status, channel, environment, architectures, developer, summary.

### `api/featured.json`

Featured packages with summary and status/channel labels.

### `api/search.json`

Flattened search entries with `search_blob` for client-side filtering.

### `api/channels.json`

Packages grouped by release channel.

### Other endpoints

- `api/tweak_release.json` — full metadata
- `api/repo_settings.json` — repo config
- `api/about.json` — compiler version info

---

## Multi-Version Packages

- Older `.deb` files coexist in the package directory
- Latest version is also published as `docs/pkg/<bundle_id>.deb` (the default download)
- Older versions keep their original filenames
- Repo metadata uses the newest version
- Users can long-press a package in Sileo/Cydia to pick a different version

---

## Customisation

Main customisable files in `Styles/`:

- `index.mustache` — homepage template
- `tweak.mustache` — package depiction template
- `index.css` — shared styles
- `index.js` — homepage filtering and JS behaviour
- `settings.json` — repo metadata, branding, announcements

---

## Quick start

1. Copy `Packages/ExamplePackage/` to a new directory
2. Replace `silex_data/index.json`
3. Replace `silex_data/description.md`
4. Add your `.deb`
5. Optionally add icon, banner, and screenshots
6. Run `python3 index.py`

---

## Notes for public forks

- Remove personal package files from `Packages/`
- Remove compiled output from `docs/` (unless this repo is also your live host)
- Replace example maintainer/domain values in `Styles/settings.json`
- Check announcements and example links before publishing
- Review `ok.sh` remote config before pushing

---

## License

See `LICENSE`.
