import pystache
import json
import datetime
import os
import shutil
import mistune
import random
from subprocess import check_output
from util.PackageLister import PackageLister


class DepictionGenerator:
    """
    DepictionGenerator deals with the rendering and generating of depictions.
    """

    def __init__(self, version):
        super(DepictionGenerator, self).__init__()
        self.version = version
        self.root = os.path.dirname(os.path.abspath(__file__)) + "/../"
        self.PackageLister = PackageLister(self.version)

    def CleanUp(self):
        """
        Cleans up generated output while preserving repo package artifacts.
        """
        for relative_dir in ("docs/api", "docs/assets", "docs/depiction", "docs/web", "temp"):
            try:
                shutil.rmtree(os.path.join(self.root, relative_dir))
            except Exception:
                pass

        for relative_file in (
            "docs/404.html",
            "docs/CNAME",
            "docs/CydiaIcon.png",
            "docs/index.html",
            "docs/Packages",
            "docs/Packages.bz2",
            "docs/Packages.xz",
            "docs/Packages.zst",
            "docs/Release",
            "docs/sileo-featured.json",
        ):
            try:
                os.remove(os.path.join(self.root, relative_file))
            except Exception:
                pass

    def _label_from_value(self, value, fallback):
        if not value:
            return fallback
        return str(value).replace("_", " ").replace("-", " ").title()

    def _list_field(self, package, field):
        if field not in package:
            return []
        value = package.get(field, [])
        if isinstance(value, str):
            value = [value]
        return [entry for entry in value if entry]

    def _normalize_package(self, tweak_data):
        package = dict(tweak_data)

        package['show_status_badge'] = bool(tweak_data.get('status'))
        package['show_channel_badge'] = bool(tweak_data.get('release_channel'))
        package['status'] = package.get('status', 'active')
        package['status_label'] = self._label_from_value(package['status'], 'Active')
        package['channel'] = package.get('release_channel', 'stable')
        package['channel_label'] = self._label_from_value(package['channel'], 'Stable')

        package['install_env'] = self._list_field(package, 'install_env')
        package['has_install_env'] = len(package['install_env']) > 0
        package['install_env_text'] = " / ".join(package['install_env']) if package['install_env'] else ""

        package['injection'] = self._list_field(package, 'injection')
        package['has_injection'] = len(package['injection']) > 0
        package['injection_text'] = ", ".join(package['injection']) if package['injection'] else ""

        architectures = self._list_field(package, 'architectures')
        if not architectures:
            architecture = package.get('architecture')
            if architecture:
                architectures = [architecture]
        package['architectures'] = architectures
        package['show_arch_badge'] = bool(tweak_data.get('architectures')) and len(architectures) > 0
        package['architectures_text'] = ", ".join(architectures) if architectures else package.get('architecture', '')

        for field in ('install_notes', 'known_conflicts', 'replaces_notice', 'search_keywords'):
            package[field] = self._list_field(package, field)
            package['has_' + field] = len(package[field]) > 0

        social_entries = []
        for entry in package.get('social', []):
            if entry.get('name') and entry.get('url'):
                social_entries.append(entry)
        package['social_entries'] = social_entries
        package['has_social'] = len(social_entries) > 0
        package['has_homepage'] = bool(package.get('homepage'))
        package['has_source'] = bool(package.get('source'))
        package['has_tint'] = bool(package.get('tint'))
        package['has_description_md'] = self.PackageLister.PackageHasDescription(package)
        package['summary'] = self.PackageLister.PackageDescriptionPreview(package, 140)
        package['compatibility_text'] = package['works_min'] + " to " + package['works_max']
        package['has_badges'] = (
            package['show_status_badge']
            or package['show_channel_badge']
            or package['has_install_env']
            or package['show_arch_badge']
        )
        package['has_compat_matrix'] = (
            package['has_install_env']
            or package['has_injection']
            or len(architectures) > 1
        )
        package['has_package_tags'] = package['has_homepage'] or package['has_source']
        package['search_blob'] = " ".join([
            package.get('name', ''),
            package.get('bundle_id', ''),
            package.get('section', ''),
            package.get('developer', {}).get('name', ''),
            package['install_env_text'],
            package['architectures_text'],
            " ".join(package['search_keywords'])
        ]).strip()
        return package

    def _render_badges_html(self, package):
        badges = []
        if package['show_status_badge']:
            badges.append('<span class="meta-badge meta-badge-{0}">{1}</span>'.format(package['status'], package['status_label']))
        if package['show_channel_badge']:
            badges.append('<span class="meta-badge meta-badge-{0}">{1}</span>'.format(package['channel'], package['channel_label']))
        if package['has_install_env']:
            badges.append('<span class="meta-badge">{0}</span>'.format(package['install_env_text']))
        if package['show_arch_badge']:
            badges.append('<span class="meta-badge">{0}</span>'.format(package['architectures_text']))
        return "".join(badges)

    def _render_native_metadata_markdown(self, package):
        lines = []
        if package['show_status_badge']:
            lines.append('**状态 Status**: {0}'.format(package['status_label']))
        if package['show_channel_badge']:
            lines.append('**渠道 Channel**: {0}'.format(package['channel_label']))
        if package['has_install_env']:
            lines.append('**环境 Environment**: {0}'.format(package['install_env_text']))
        if package['has_injection']:
            lines.append('**注入 Injection**: {0}'.format(package['injection_text']))
        if package['show_arch_badge']:
            lines.append('**架构 Architectures**: {0}'.format(package['architectures_text']))
        if not lines:
            return ''
        return '  \n'.join(lines)

    def _render_info_list_html(self, title, items):
        if not items:
            return ""
        rendered = ['<h3>{0}</h3><div class="info-list">'.format(title)]
        for item in items:
            rendered.append('<div class="info-list-item">{0}</div>'.format(item))
        rendered.append('</div>')
        return "".join(rendered)

    def _render_compatibility_matrix_html(self, package):
        if not package.get('has_compat_matrix'):
            return ""
        blocks = []
        if package['has_install_env']:
            blocks.append(('Install Environment', package['install_env_text']))
        if package['has_injection']:
            blocks.append(('Injection', package['injection_text']))
        if len(package['architectures']) > 1:
            blocks.append(('Architectures', package['architectures_text']))
        if package['show_channel_badge']:
            blocks.append(('Release Channel', package['channel_label']))
        if not blocks:
            return ""
        html = ['<h3>兼容信息 Compatibility</h3><div class="matrix-grid">']
        for title, text in blocks:
            html.append('<div class="matrix-item"><div class="matrix-title">{0}</div><div class="matrix-text">{1}</div></div>'.format(title, text))
        html.append('</div>')
        return "".join(html)

    def _render_changelog_markdown(self, version):
        changes = version.get('changes', '')
        if isinstance(changes, dict):
            parts = []
            for key in ('new', 'fix', 'improve', 'remove', 'note'):
                entries = changes.get(key, [])
                if entries:
                    parts.append('**{0}**'.format(self._label_from_value(key, key.title())))
                    for entry in entries:
                        parts.append('- ' + entry)
                    parts.append('')
            return "\n".join(parts).strip()
        return str(changes).replace('\n', '  \n')

    def _prepare_repo_announcements(self, repo_settings):
        announcements = repo_settings.get('announcements', [])
        normalized = []
        for entry in announcements:
            if entry.get('title') and entry.get('message'):
                normalized.append({
                    'level': entry.get('level', 'info'),
                    'title': entry['title'],
                    'message': entry['message']
                })
        return normalized

    def RenderPackageHTML(self, tweak_data):
        package = self._normalize_package(tweak_data)
        with open(self.root + 'Styles/tweak.mustache', 'r') as content_file:
            template = content_file.read()
            replacements = DepictionGenerator.RenderDataHTML(self)
            replacements['tweak_name'] = package['name'] + (' (Roothide)' if package.get('section') == 'Roothide' else '')
            replacements['tweak_developer'] = package['developer']['name']
            replacements['tweak_compatibility'] = package['compatibility_text']
            replacements['tweak_version'] = package['version']
            replacements['tweak_section'] = package['section']
            replacements['tweak_bundle_id'] = package['bundle_id']
            replacements['works_min'] = package['works_min']
            replacements['works_max'] = package['works_max']
            replacements['tweak_tagline'] = package['tagline']
            replacements['tweak_carousel'] = DepictionGenerator.ScreenshotCarousel(self, package)
            replacements['tweak_changelog'] = DepictionGenerator.RenderChangelogHTML(self, package)
            replacements['footer'] = DepictionGenerator.RenderFooter(self)
            replacements['has_homepage'] = package['has_homepage']
            replacements['homepage'] = package.get('homepage', '')
            replacements['has_source'] = package['has_source']
            replacements['source'] = package.get('source', '')
            replacements['has_social'] = package['has_social']
            replacements['has_tint'] = package['has_tint']
            replacements['has_description_md'] = package['has_description_md']
            replacements['social_entries'] = package['social_entries']
            replacements['has_badges'] = package['has_badges']
            replacements['has_compat_matrix'] = package['has_compat_matrix']
            replacements['support_badges_html'] = self._render_badges_html(package)
            replacements['compatibility_matrix_html'] = self._render_compatibility_matrix_html(package)
            replacements['install_notes_html'] = self._render_info_list_html('安装说明 Install Notes', package['install_notes'])
            replacements['known_conflicts_html'] = self._render_info_list_html('已知冲突 Known Conflicts', package['known_conflicts'])
            replacements['replaces_html'] = self._render_info_list_html('迁移与替代 Migration & Replacement', package['replaces_notice'])
            replacements['tint_color'] = package.get('tint', PackageLister.GetRepoSettings(self).get('tint', '#2cb1be'))

            try:
                with open(self.root + 'docs/assets/' + package['bundle_id'] + '/description.md', 'r') as md_file:
                    replacements['tweak_description'] = mistune.markdown(md_file.read())
            except Exception:
                replacements['tweak_description'] = package['tagline']

            return pystache.render(template, replacements)

    def RenderPackageNative(self, tweak_data):
        package = self._normalize_package(tweak_data)
        repo_settings = PackageLister.GetRepoSettings(self)
        tint = package.get('tint', repo_settings.get('tint', '#2cb1be'))
        subfolder = PackageLister.FullPathCname(self, repo_settings)

        try:
            with open(self.root + 'docs/assets/' + package['bundle_id'] + '/description.md', 'r') as md_file:
                md_txt = md_file.read()
        except Exception:
            md_txt = package['tagline']

        image_list = self.PackageLister.GetScreenshots(package)
        screenshot_obj = []
        if image_list:
            for image in image_list:
                screenshot_obj.append({
                    'url': 'https://' + repo_settings['cname'] + subfolder + '/assets/' + package['bundle_id'] + '/screenshot/' + image,
                    'accessibilityText': 'Screenshot'
                })
            screenshot_view_carousel = 'DepictionScreenshotsView'
        else:
            screenshot_view_carousel = 'HiddenDepictionScreenshotsView'

        info_views = [
            {
                'class': screenshot_view_carousel,
                'screenshots': screenshot_obj,
                'itemCornerRadius': 8,
                'itemSize': PackageLister.GetScreenshotSize(self, package)
            },
            {
                'markdown': md_txt,
                'useSpacing': 'true',
                'class': 'DepictionMarkdownView'
            },
            {'class': 'DepictionHeaderView', 'title': '插件信息 Info'},
            {'class': 'DepictionTableTextView', 'title': '开发者 Developer', 'text': package['developer']['name']},
            {'class': 'DepictionTableTextView', 'title': '版本 Version', 'text': package['version']},
            {'class': 'DepictionTableTextView', 'title': '兼容性 Compatibility', 'text': package['works_min'] + ' 至 ' + package['works_max']},
            {'class': 'DepictionTableTextView', 'title': '分类 Section', 'text': package['section']}
        ]

        metadata_markdown = self._render_native_metadata_markdown(package)
        if metadata_markdown:
            info_views.extend([
                {'class': 'DepictionMarkdownView', 'markdown': metadata_markdown},
                {'class': 'DepictionSpacerView'}
            ])
        else:
            info_views.append({'class': 'DepictionSpacerView'})

        for note_group in (
            ('安装说明 Install Notes', package['install_notes']),
            ('已知冲突 Known Conflicts', package['known_conflicts']),
            ('迁移与替代 Migration & Replacement', package['replaces_notice'])
        ):
            if note_group[1]:
                markdown = '#### {0}\n\n'.format(note_group[0]) + '\n'.join(['- ' + item for item in note_group[1]])
                info_views.append({'class': 'DepictionMarkdownView', 'markdown': markdown})

        if package.get('homepage'):
            info_views.append({'class': 'DepictionTableButtonView', 'title': '项目主页 Homepage', 'action': package['homepage'], 'openExternal': 'true', 'tintColor': tint})
        if package.get('source'):
            info_views.append({'class': 'DepictionTableButtonView', 'title': '源代码 Source Code', 'action': package['source'], 'openExternal': 'true', 'tintColor': tint})
        for entry in package['social_entries']:
            info_views.append({'class': 'DepictionTableButtonView', 'title': entry['name'], 'action': entry['url'], 'openExternal': 'true', 'tintColor': tint})

        info_views.extend([
            {'class': 'DepictionSpacerView'},
            {
                'class': 'DepictionTableButtonView',
                'title': '联系支持 Contact Support',
                'action': 'depiction-https://' + repo_settings['cname'] + subfolder + '/depiction/native/help/' + package['bundle_id'] + '.json',
                'openExternal': 'true',
                'tintColor': tint
            },
            {
                'class': 'DepictionLabelView',
                'text': DepictionGenerator.RenderFooter(self),
                'textColor': '#999999',
                'fontSize': '10.0',
                'alignment': 1
            }
        ])

        depiction = {
            'minVersion': '0.1',
            'headerImage': 'https://' + repo_settings['cname'] + subfolder + '/assets/' + package['bundle_id'] + '/banner.png',
            'tintColor': tint,
            'tabs': [
                {'tabname': '详情 Details', 'views': info_views, 'class': 'DepictionStackView'},
                {'tabname': '更新日志 Changelog', 'views': DepictionGenerator.RenderNativeChangelog(self, package), 'class': 'DepictionStackView'}
            ],
            'class': 'DepictionTabView'
        }
        return json.dumps(depiction, separators=(',', ':'))

    def RenderNativeChangelog(self, tweak_data):
        try:
            changelog = []
            versions = tweak_data.get('changelog', [])
            limit = tweak_data.get('changelog_limit')
            if limit:
                versions = versions[-int(limit):]
            for version in versions[::-1]:
                changelog.append({
                    'class': 'DepictionMarkdownView',
                    'markdown': '#### 版本 {0}\n\n{1}'.format(version['version'], self._render_changelog_markdown(version))
                })
            changelog.append({
                'class': 'DepictionLabelView',
                'text': DepictionGenerator.RenderFooter(self),
                'textColor': '#999999',
                'fontSize': '10.0',
                'alignment': 1
            })
            return changelog
        except Exception:
            return [
                {'class': 'DepictionHeaderView', 'title': '更新日志 Changelog'},
                {'class': 'DepictionMarkdownView', 'markdown': '暂无更新日志。No changelog yet.'},
                {'class': 'DepictionLabelView', 'text': DepictionGenerator.RenderFooter(self), 'textColor': '#999999', 'fontSize': '10.0', 'alignment': 1}
            ]

    def ChangelogEntry(self, version, raw_md):
        md_text = raw_md.replace('\n', '  \n')
        return '''<div class="changelog_entry">
                <h4>{0}</h4>
                <div class="md_view">{1}</div>
            </div>'''.format(version, mistune.markdown(md_text))

    def RenderChangelogHTML(self, tweak_data):
        element = ''
        try:
            versions = tweak_data.get('changelog', [])
            limit = tweak_data.get('changelog_limit')
            if limit:
                versions = versions[-int(limit):]
            for version in versions[::-1]:
                element += DepictionGenerator.ChangelogEntry(self, version['version'], self._render_changelog_markdown(version))
            return element
        except Exception:
            return '暂无更新日志。No changelog yet.'

    def RenderIndexHTML(self):
        repo_settings = PackageLister.GetRepoSettings(self)
        with open(self.root + 'Styles/index.mustache', 'r') as content_file:
            template = content_file.read()
            replacements = DepictionGenerator.RenderDataHTML(self)
            replacements['tint_color'] = repo_settings['tint']
            replacements['footer'] = DepictionGenerator.RenderFooter(self)

            tweak_release = [self._normalize_package(tweak) for tweak in PackageLister.GetTweakRelease(self)]
            sections = {}
            featured_packages = []
            channels = {}

            for tweak in tweak_release:
                if tweak.get('featured', '').lower() == 'true':
                    featured_packages.append(tweak)
                section_name = tweak.get('section', 'Other')
                sections.setdefault(section_name, []).append(tweak)
                channels[tweak['channel_label']] = channels.get(tweak['channel_label'], 0) + 1

            replacements['sections'] = [{'section_name': key, 'packages': value} for key, value in sections.items()]
            replacements['featured_packages'] = featured_packages
            replacements['has_featured_packages'] = len(featured_packages) > 0
            replacements['package_count'] = len(tweak_release)
            replacements['channels'] = [{'name': key, 'count': value} for key, value in channels.items()]
            replacements['announcements'] = self._prepare_repo_announcements(repo_settings)
            replacements['has_announcements'] = len(replacements['announcements']) > 0
            return pystache.render(template, replacements)

    def RenderFooter(self):
        repo_settings = PackageLister.GetRepoSettings(self)
        data = DepictionGenerator.RenderDataHTML(self)
        try:
            return pystache.render(repo_settings['footer'], data)
        except Exception:
            return pystache.render('Silex {{silex_version}} – Updated {{silex_compile_date}}', data)

    def RenderDataBasic(self):
        repo_settings = PackageLister.GetRepoSettings(self)
        with open(self.root + 'Styles/settings.json', 'r') as content_file:
            data = json.load(content_file)
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            subfolder = PackageLister.FullPathCname(self, repo_settings)
            return {
                'silex_version': self.version,
                'silex_compile_date': date,
                'repo_name': data['name'],
                'repo_url': data['cname'] + subfolder,
                'repo_desc': data['description'],
                'repo_tint': data['tint']
            }

    def RenderDataHTML(self):
        data = DepictionGenerator.RenderDataBasic(self)
        tweak_release = PackageLister.GetTweakRelease(self)
        data['repo_packages'] = DepictionGenerator.PackageEntryList(self, tweak_release)
        data['repo_carousel'] = DepictionGenerator.CarouselEntryList(self, tweak_release)
        return data

    def PackageEntry(self, name, author, icon, bundle_id):
        if bundle_id != 'silex_do_not_hyperlink':
            return '''<a class="subtle_link" href="depiction/web/{3}.html"><div class="package">
            <img src="{0}">
            <div class="package_info">
                <p class="package_name">{1}</p>
                <p class="package_caption">{2}</p>
            </div>
        </div></a>'''.format(icon, name, author, bundle_id)
        return '''<div class="package">
                <img src="{0}">
                <div class="package_info">
                    <p class="package_name">{1}</p>
                    <p class="package_caption">{2}</p>
                </div>
            </div>'''.format(icon, name, author)

    def ScreenshotCarousel(self, tweak_data):
        screenshot_div = '<div class="scroll_view">'
        image_list = self.PackageLister.GetScreenshots(tweak_data)
        if image_list:
            for image in image_list:
                screenshot_div += '''<img class="img_card" src="../../assets/{0}/screenshot/{1}">'''.format(tweak_data['bundle_id'], image)
            screenshot_div += '</div>'
        else:
            screenshot_div = ''
        return screenshot_div

    def CarouselEntry(self, name, banner, bundle_id):
        if len(name) > 18:
            name = name[:18] + '…'
        return '''<a href="depiction/web/{0}.html" style="background-image: url({1})" class="card">
                <p>{2}</p>
            </a>'''.format(bundle_id, banner, name)

    def NativeFeaturedCarousel(self, tweak_release):
        repo_settings = PackageLister.GetRepoSettings(self)
        subfolder = PackageLister.FullPathCname(self, repo_settings)
        banners = []
        for package in tweak_release:
            try:
                if package['featured'].lower() == 'true':
                    banners.append({
                        'package': package['bundle_id'],
                        'title': package['name'],
                        'url': 'https://' + repo_settings['cname'] + subfolder + '/assets/' + package['bundle_id'] + '/banner.png',
                        'hideShadow': 'false'
                    })
            except Exception:
                pass
        if not banners:
            try:
                featured_package = tweak_release[random.randint(0, len(tweak_release) - 1)]
                banners.append({
                    'package': featured_package['bundle_id'],
                    'title': featured_package['name'],
                    'url': 'https://' + repo_settings['cname'] + subfolder + '/assets/' + featured_package['bundle_id'] + '/banner.png',
                    'hideShadow': 'false'
                })
            except Exception:
                PackageLister.ErrorReporter(self, 'Configuration Error!', 'You have no packages added to this repo.')
        return json.dumps({'class': 'FeaturedBannersView', 'itemSize': '{263, 148}', 'itemCornerRadius': 8, 'banners': banners}, separators=(',', ':'))

    def PackageEntryList(self, tweak_release):
        list_el = ''
        for package in tweak_release:
            list_el += DepictionGenerator.PackageEntry(self, package['name'], package['developer']['name'], 'assets/' + package['bundle_id'] + '/icon.png', package['bundle_id'])
        return list_el

    def CarouselEntryList(self, tweak_release):
        list_el = ''
        for package in tweak_release:
            try:
                if package['featured'].lower() == 'true':
                    list_el += DepictionGenerator.CarouselEntry(self, package['name'], 'assets/' + package['bundle_id'] + '/banner.png', package['bundle_id'])
            except Exception:
                pass
        if list_el == '':
            try:
                featured_package = tweak_release[random.randint(0, len(tweak_release) - 1)]
                list_el += DepictionGenerator.CarouselEntry(self, featured_package['name'], 'assets/' + featured_package['bundle_id'] + '/banner.png', featured_package['bundle_id'])
            except Exception:
                PackageLister.ErrorReporter(self, 'Configuration Error!', 'You have no packages added to this repo.')
        return list_el

    def SilexAbout(self):
        compile_date = datetime.datetime.now().isoformat()
        try:
            upstream_url = check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=self.root).decode('utf-8')
        except Exception:
            upstream_url = 'undefined'
        return {
            'software': 'Silex',
            'version': self.version,
            'compile_date': compile_date,
            'upstream_url': upstream_url
        }

    def RenderVersionAPI(self, tweak_release):
        compile_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        result = {}
        for tweak in tweak_release:
            package = self._normalize_package(tweak)
            result[package['bundle_id']] = {'version': package['version'], 'date': compile_date, 'name': package['name']}
        return json.dumps(result, separators=(',', ':'))

    def RenderPackagesAPI(self, tweak_release):
        packages = []
        for tweak in tweak_release:
            package = self._normalize_package(tweak)
            packages.append({
                'bundle_id': package['bundle_id'],
                'name': package['name'],
                'version': package['version'],
                'section': package['section'],
                'works_min': package['works_min'],
                'works_max': package['works_max'],
                'featured': package.get('featured', 'false').lower() == 'true',
                'status': package['status'],
                'release_channel': package['channel'],
                'install_env': package['install_env'],
                'architectures': package['architectures'],
                'developer': package['developer'].get('name', ''),
                'summary': package['summary']
            })
        return json.dumps(packages, separators=(',', ':'))

    def RenderFeaturedAPI(self, tweak_release):
        featured = []
        for tweak in tweak_release:
            package = self._normalize_package(tweak)
            if package.get('featured', '').lower() == 'true':
                featured.append({
                    'bundle_id': package['bundle_id'],
                    'name': package['name'],
                    'summary': package['summary'],
                    'status': package['status'],
                    'release_channel': package['channel']
                })
        return json.dumps(featured, separators=(',', ':'))

    def RenderSearchAPI(self, tweak_release):
        entries = []
        for tweak in tweak_release:
            package = self._normalize_package(tweak)
            entries.append({
                'bundle_id': package['bundle_id'],
                'name': package['name'],
                'developer': package['developer'].get('name', ''),
                'section': package['section'],
                'status': package['status'],
                'release_channel': package['channel'],
                'install_env': package['install_env'],
                'architectures': package['architectures'],
                'keywords': package['search_keywords'],
                'search_blob': package['search_blob']
            })
        return json.dumps(entries, separators=(',', ':'))

    def RenderChannelsAPI(self, tweak_release):
        channels = {}
        for tweak in tweak_release:
            package = self._normalize_package(tweak)
            channels.setdefault(package['channel'], []).append({
                'bundle_id': package['bundle_id'],
                'name': package['name'],
                'version': package['version'],
                'status': package['status']
            })
        return json.dumps(channels, separators=(',', ':'))

    def RenderNativeHelp(self, tweak_data):
        package = self._normalize_package(tweak_data)
        repo_settings = PackageLister.GetRepoSettings(self)
        tint = package.get('tint', repo_settings.get('tint', '#2cb1be'))
        view = []
        try:
            if package['developer']['email']:
                view.append({'class': 'DepictionMarkdownView', 'markdown': 'If you need help with "' + package['name'] + '", you can contact ' + package['developer']['name'] + ', the developer, via e-mail.'})
                view.append({'class': 'DepictionTableButtonView', 'title': 'Email Developer', 'action': 'mailto:' + package['developer']['email'], 'openExternal': 'true', 'tintColor': tint})
        except Exception:
            pass

        for entry in package['social_entries']:
            view.append({'class': 'DepictionTableButtonView', 'title': entry['name'], 'action': entry['url'], 'openExternal': 'true', 'tintColor': tint})

        try:
            if package['maintainer']['email']:
                view.append({'class': 'DepictionTableButtonView', 'title': 'Email Maintainer', 'action': 'mailto:' + package['maintainer']['email'], 'openExternal': 'true', 'tintColor': tint})
        except Exception:
            pass

        view.append({'class': 'DepictionMarkdownView', 'markdown': 'If you found a mistake in the depiction or cannot download the package, you can reach out to the maintainer of the "' + repo_settings['name'] + '" repo, ' + repo_settings['maintainer']['name'] + '.'})
        view.append({'class': 'DepictionTableButtonView', 'title': 'Email Repo Maintainer', 'action': 'mailto:' + repo_settings['maintainer']['email'], 'openExternal': 'true', 'tintColor': tint})

        for entry in repo_settings.get('social', []):
            if entry.get('name') and entry.get('url'):
                view.append({'class': 'DepictionTableButtonView', 'title': entry['name'], 'action': entry['url'], 'openExternal': 'true', 'tintColor': tint})

        return json.dumps({'class': 'DepictionStackView', 'tintColor': tint, 'title': 'Contact Support', 'views': view}, separators=(',', ':'))
