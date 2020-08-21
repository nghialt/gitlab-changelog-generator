import datetime
import dateutil.parser
import semver
import os.path
import re

from changelog_generator.calls import (
    get_commits_until_latest_bump,
)
from changelog_generator.log_handlers import logger


class ZPWGenerator:
    include_projs = []
    
    patch_types = {
        'fix': None,
        'chore': None,
        'test': None,
        '': None,
    }
    minor_types = {
        'feat': None,
        'chg': None,
        'vendor': None,
    }
    type_map = {
        'fix': 'Fixed',
        'feat': 'Added',
        'chg': 'Changes',
        'chore': 'Additions',
        'test': 'Tests',
        'vendor': 'Vendors',
        '': 'Others',
    }
    file_path = f'CHANGELOG.md'

    type_order = ['feat', 'chg', 'fix', 'chore', 'test', '', ]

    def generate_changelog(self, cli_args: dict) -> str:
        # Get any commits since that date
        new_commits = get_commits_until_latest_bump(cli_args)

        # Get the current date so that we can add it to the CHANGELOG.md document
        date = datetime.datetime.now()
        current_date = date.strftime('%Y/%m/%d')

        allowed_projs = self.include_projs
        allowed_projs.append(cli_args['sub_project'])
        logger.debug('allow_projs')
        logger.debug(allowed_projs)

        commits_type_dict = {
            type: [] for type in self.type_map
        }
        commits_type_dict[''] = []
        for commit in new_commits:
            title = commit['title']
            match_obj = re.match(r'^(.+)(\((.+)\))?:', title)
            change_type = ''
            if match_obj:
                change_type = match_obj.group(1)
                proj = match_obj.group(2)
                if proj and proj not in allowed_projs:
                    logger.info(title)
                    continue
            logger.info(title)
            if change_type in self.type_map:
                commits_type_dict[change_type].append(commit)
            else:
                commits_type_dict[''].append(commit)

        version = self.get_version(cli_args)
        version = self.get_next_version(version, commits_type_dict, cli_args)

        # Determine whether a CHANGELOG.md file already exists
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'w').close()
        with open(self.file_path, 'r') as original_changelog:
            original_changelog_data = original_changelog.readlines()
            if len(original_changelog_data) > 2:
                original_changelog_data = original_changelog_data[2:]
            with open(self.file_path, 'w') as modified_changelog:
                modified_changelog.write('# CHANGELOG\n\n')
                modified_changelog.write(f'## v{version} - {current_date}\n')
                for type in self.type_order:
                    commits = commits_type_dict[type]
                    if not commits:
                        continue
                    modified_changelog.write(
                        f'\n### {self.type_map[type]} \n'
                    )
                    for commit in commits:
                        logger.debug('commit ')
                        logger.debug(commit)
                        lines = commit['message'].strip().split('\n')
                        modified_changelog.write(
                            f"  * {commit['committed_date'][:10]} - {lines[0]}"
                        )

                        if not re.match(r'^.+\(\![0-9]+\)$', lines[0]):
                            modified_changelog.write(f" ({commit['short_id']})")

                        modified_changelog.write('\n')
                        if len(lines) > 1:
                            modified_changelog.write('\n'.join('    ' + line for line in lines[1:] if line))
                            modified_changelog.write('\n')

                modified_changelog.write(f'\n')
                modified_changelog.write(''.join(original_changelog_data))
        return f'{self.file_path} updated successfully'

    def get_version(self, cli_args: dict) -> str:
        if 'version' in cli_args:
            return cli_args['version']
        default_version = '0.0.0'
        if not os.path.isfile(self.file_path):
            return default_version
        version_regex = r'^## v([0-9\.]+) - [0-9\/]+$'
        with open(self.file_path, 'r') as original_changelog:
            line = original_changelog.readline()
            while line:
                match_obj = re.match(version_regex, line)
                if match_obj:
                    version = match_obj.group(1)
                    if version:
                        return version
                line = original_changelog.readline()
        
        return default_version

    def get_next_version(self, version, types_flags, cli_args: dict) -> str:
        if 'version' in cli_args:
            return cli_args['version']
        ver = semver.VersionInfo.parse(version)
        for type in self.minor_types:
            if type in types_flags:
                return ver.bump_minor()

        return ver.pump_patch()
