# Silex

Silex is a static APT repository generator for jailbroken iOS package feeds.

Forked from [Silica](https://github.com/Shugabuga/Silica), Silex is a more modern repo template for public or private jailbreak feeds: it keeps the original static-hosting model, but adds stronger package metadata, richer depictions, better compatibility signaling, lightweight APIs, featured package presentation, repo announcements, and searchable package browsing.

## What this fork focuses on

- Static output suitable for GitHub Pages or any static host
- Web and native depictions for every package
- Homepage package discovery instead of a plain add-source page
- Explicit package status and release channel labels
- Rootless / Roothide / Rootful install environment metadata
- Architecture-aware package presentation
- Install notes, known conflicts, and migration notices
- Multi-version package publishing support
- `tagline` → Debian `Description` injection for cleaner control metadata
- Lightweight JSON APIs for search, package listing, featured content, and version checks

## Highlights

- Automatic generation of:
  - `Release`
  - `Packages`, `Packages.bz2`, `Packages.xz`
  - web depictions
  - native depictions
  - repo APIs
- Support for `arm64` and `arm64e`
- Better support for Roothide-style distribution
- Searchable homepage with filters
- Repo-wide announcements from `Styles/settings.json`
- Structured changelog rendering
- Rich package metadata model without requiring a backend

## Project Structure

```text
Silex/
├── index.py                  # Main compiler entry
├── Packages/                 # Your packages and metadata
├── Styles/                   # Repo templates and branding assets
├── util/                     # Compiler helpers
├── docs/                     # Generated static repo output
├── compile.sh                # Optional build helper
└── requirements.txt          # Python dependencies
```

## Package Layout

Each package lives in its own folder under `Packages/`.

```text
Packages/
└── ExamplePackage/
    ├── my-package.deb
    └── silex_data/
        ├── index.json
        ├── description.md
        ├── icon.png
        ├── banner.png
        ├── screenshots/
        └── scripts/
```

Notes:

- If a `.deb` file exists in the package folder, Silex uses it as the package source.
- `silex_data/index.json` stores package metadata used by depictions, APIs, and repo generation.
- `description.md` is the main body of the package depiction.
- `icon.png`, `banner.png`, screenshots, and maintainer scripts are optional but recommended.

## Requirements

### System dependencies

macOS:

```bash
brew install dpkg gnupg
```

Debian / Ubuntu:

```bash
sudo apt-get install dpkg-dev gnupg git xz-utils bzip2
```

### Python

- Python 3
- `pip`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Main repo configuration lives in `Styles/settings.json`.

Example:

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
            "title": "Example compatibility notice",
            "message": "Replace this announcement with repo-specific guidance."
        }
    ],
    "automatic_git": "false",
    "footer": "{{repo_name}} · Updated {{silex_compile_date}}",
    "enable_gpg": "false"
}
```

### Important repo fields

- `name`: repo display name
- `description`: short repo description
- `tint`: default accent color
- `cname`: final public domain, without `https://`
- `maintainer`: repo maintainer information
- `social`: repo-level links shown in support views
- `announcements`: repo-wide warning/info banners shown on the homepage
- `automatic_git`: whether to auto-run git after compile
- `enable_gpg`: whether to sign `Release.gpg`
- `footer`: Mustache-rendered footer string

### Announcement levels

Supported `announcements[].level` values are intended for visual emphasis:

- `info`
- `warning`
- `error`
- `success`

## Package Metadata

Each package should provide a `silex_data/index.json` file.

### Minimal example

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "A short package description.",
    "developer": {
        "name": "Example Developer"
    },
    "maintainer": {
        "name": "Example Maintainer"
    },
    "section": "Tweaks",
    "architecture": "iphoneos-arm64",
    "works_min": "15.0",
    "works_max": "17.0",
    "featured": "false"
}
```

### Modern metadata example

```json
{
    "bundle_id": "com.example.package",
    "name": "Example Package",
    "version": "1.0.0",
    "tagline": "An example package used to demonstrate modern Silex metadata.",
    "homepage": "https://example.com",
    "source": "https://github.com/example/example-package",
    "developer": {
        "name": "Example Developer",
        "email": "developer@example.com"
    },
    "maintainer": {
        "name": "Example Maintainer",
        "email": "maintainer@example.com"
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
        "Restart the target app after changing settings."
    ],
    "known_conflicts": [
        "Do not install together with ExampleConflict."
    ],
    "replaces_notice": [
        "This package replaces the older legacy layout."
    ],
    "search_keywords": ["example", "rootless", "roothide"],
    "changelog_limit": 3,
    "changelog": [
        {
            "version": "1.0.0",
            "changes": {
                "new": ["Added modern metadata examples."],
                "improve": ["Improved depiction output."]
            }
        }
    ]
}
```

## Metadata field reference

### Core fields

- `bundle_id`: package identifier
- `name`: package display name
- `version`: current package version
- `tagline`: short summary, also used as Debian `Description`
- `section`: package category
- `works_min`: minimum supported iOS version
- `works_max`: maximum supported iOS version

### Repo and depiction fields

- `homepage`: project homepage link
- `source`: source code link
- `social`: developer links displayed in depictions
- `tint`: package-specific accent color
- `featured`: whether the package appears in featured sections
- `description.md`: full Markdown depiction body

### Compatibility and environment fields

- `architecture`: primary Debian architecture
- `architectures`: list of architectures shown in the UI and APIs
- `install_env`: install environments such as `rootless`, `roothide`, `rootful`
- `injection`: hook/injection ecosystem labels such as `ellekit`

### Status and release fields

- `status`: package lifecycle state, such as:
  - `active`
  - `beta`
  - `experimental`
  - `deprecated`
  - `internal`
  - `archived`
- `release_channel`: release stream, such as:
  - `stable`
  - `beta`
  - `nightly`
  - `experimental`

### Guidance and migration fields

- `install_notes`: installation or usage notes shown on depictions
- `known_conflicts`: warnings about incompatible packages or setups
- `replaces_notice`: migration and replacement guidance
- `search_keywords`: additional search terms for homepage/API search

### Changelog fields

Silex supports both plain-text changelog entries and structured changelog sections.

#### Plain text format

```json
{
    "version": "1.0.0",
    "changes": "Fixed crashes and improved startup speed."
}
```

#### Structured format

```json
{
    "version": "1.0.0",
    "changes": {
        "new": ["Added rootless support."],
        "fix": ["Fixed settings crash on iOS 16."],
        "improve": ["Improved injection reliability."]
    }
}
```

Optional structured keys commonly used:

- `new`
- `fix`
- `improve`
- `remove`
- `note`

Use `changelog_limit` to limit how many recent changelog entries are rendered.

## Description files and assets

### `description.md`

`description.md` is the main long-form depiction body.

Use it for:

- package overview
- feature lists
- compatibility notes
- setup instructions
- migration notes
- support guidance

If `description.md` is missing, Silex falls back to `tagline`.

### Optional assets

- `icon.png`: package icon
- `banner.png`: package banner
- `screenshots/`: screenshot carousel images
- `scripts/`: maintainer scripts copied into `DEBIAN/`

## Homepage behavior

The generated homepage is designed to behave more like a package portal than a plain add-source page.

It includes:

- repo announcements
- featured packages
- section-based browsing
- client add-source buttons
- search and filter controls
- status, channel, environment, and architecture badges

Current homepage filters support:

- search text
- package status
- release channel
- install environment

## Depictions

### Web depictions

The web package page can show:

- banner and icon
- package summary and Markdown description
- status and release channel badges
- compatibility matrix
- install notes
- known conflicts
- migration/replacement notices
- screenshots
- homepage/source/social links
- changelog tabs

### Native depictions

The native depiction output is generated for Sileo-style clients and includes:

- screenshots
- Markdown content
- package metadata tables
- compatibility/environment labels
- install notes and conflict notices
- support actions
- changelog tab

## Build

Run the compiler from the repo root:

```bash
python3 index.py
```

Or use the helper script:

```bash
./compile.sh
```

After a successful build, Silex generates the static repo into `docs/`.

## Output

The generated `docs/` directory includes:

- `Packages`, `Packages.bz2`, `Packages.xz`
- `Release` and optional `Release.gpg`
- `pkg/` package files
- `depiction/web/` HTML depictions
- `depiction/native/` native depiction JSON
- `assets/` icons, banners, descriptions, screenshots
- `api/` JSON API endpoints

## API Endpoints

Silex generates lightweight JSON endpoints under `docs/api/`.

### `api/version.json`

Compact version lookup map keyed by bundle ID.

Example:

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

Lightweight package list for repo frontends, apps, or external tooling.

Typical fields include:

- `bundle_id`
- `name`
- `version`
- `section`
- `works_min`
- `works_max`
- `featured`
- `status`
- `release_channel`
- `install_env`
- `architectures`
- `developer`
- `summary`

### `api/featured.json`

List of featured packages with summary and status/channel labels.

### `api/search.json`

Flattened search-oriented entries including:

- package identity
- developer
- section
- status
- channel
- environments
- architectures
- keywords
- merged `search_blob`

### `api/channels.json`

Packages grouped by release channel.

### Other generated endpoints

- `api/tweak_release.json`
- `api/repo_settings.json`
- `api/about.json`

## Multi-Version Package Behavior

This fork supports keeping multiple package versions available at the same time.

Behavior summary:

- Older `.deb` files can coexist in the package folder
- The newest package is published as `docs/pkg/<bundle_id>.deb`
- Older versions are copied with their original filenames
- Repo metadata is generated from the newest available package version

## Customization

Main customizable files in `Styles/`:

- `index.mustache`: homepage template
- `tweak.mustache`: package depiction template
- `index.css`: shared styles
- `index.js`: homepage filtering and depiction behavior
- `settings.json`: repo metadata, branding, announcements, and maintainer links

## Quick start for new packages

The fastest way to add a package is:

1. Copy `Packages/ExamplePackage/` to a new folder
2. Replace `silex_data/index.json`
3. Replace `silex_data/description.md`
4. Add your `.deb`
5. Optionally add icon, banner, and screenshots
6. Run `python3 index.py`

## Notes for public releases

If you plan to publish your fork publicly, it is recommended that you:

- remove personal package files from `Packages/`
- remove compiled output from `docs/` before sharing the source repo, unless this repo is also your published static host
- replace example maintainer/domain values in `Styles/settings.json`
- review scripts before enabling `automatic_git` or `enable_gpg`
- check announcements and example links before publishing

## License

See `LICENSE` for the project license.
