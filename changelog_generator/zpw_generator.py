import datetime
import dateutil.parser
import semver
import os.path
import re

from changelog_generator.calls import (
    get_closed_issues_for_project,
    get_commits_since_date,
    get_last_commit_date,
    get_last_tagged_release_date,
    get_commits_until_latest_bump,
)
from changelog_generator.log_handlers import logger


class ZPWGenerator:
    include_projs = []
    
    patch_types = {
        "fix": None,
        "chore": None,
        "test": None,
        "": None,
    }
    minor_types = {
        "feat": None,
        "chg": None,
    }
    type_map = {
        "fix": "Fixed",
        "feat": "Added",
        "chg": "Changes",
        "chore": "Additions",
        "test": "Tests",
        "": "Others",
    }
    file_path = f"CHANGELOG.md"

    type_order = ["feat", "chg", "fix", "chore", "test", "", ]

    def generate_changelog(self, cli_args: dict) -> str:
        # Get any commits since that date
        new_commits = get_commits_until_latest_bump(cli_args)

        # Get the current date so that we can add it to the CHANGELOG.md document
        date = datetime.datetime.now()
        current_date = date.strftime("%Y-%m-%d")

        allowed_projs = self.include_projs
        allowed_projs.append(cli_args["sub_project"])
        logger.debug("allow_projs")
        logger.debug(allowed_projs)

        commits_type_dict = {
            type: [] for type in self.type_map
        }
        commits_type_dict[""] = []
        for commit in new_commits:
            title = commit["title"]
            match_obj = re.match(r'^(.+)(\((.+)\))?:', title)
            change_type = ""
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
                commits_type_dict[""].append(commit)

        # Determine whether a CHANGELOG.md file already exists
        if not os.path.isfile(self.file_path):
            open(self.file_path, 'a').close()
        with open(self.file_path, "r") as original_changelog:
            original_changelog_data = original_changelog.read()
            with open(self.file_path, "w") as modified_changelog:
                version = self.get_version(cli_args)
                version = self.get_next_version(version, commits_type_dict, cli_args)
                modified_changelog.write(f"## v{version} ({current_date})\n")
                for type in self.type_order:
                    commits = commits_type_dict[type]
                    if not commits:
                        continue
                    modified_changelog.write(
                        f"\n### {self.type_map[type]} \n"
                    )
                    for commit in commits:
                        modified_changelog.write("\n")
                        logger.debug("commit ")
                        logger.debug(commit)
                        lines = commit["message"].split("\n")
                        modified_changelog.write(
                            f"  * {commit['committed_date'][:10]} - {lines[0]} \n"
                        )
                        modified_changelog.write("\n".join("    " + line for line in lines[1:] if line))
                        modified_changelog.write("\n")

                modified_changelog.write(f"\n")
                modified_changelog.write(original_changelog_data)
                return f"{self.file_path} updated successfully"


    def get_closed_issues_since_last_tag(self, cli_args: dict) -> list:
        last_tagged_release_date = get_last_tagged_release_date(cli_args)

        closed_issues = get_closed_issues_for_project(cli_args)

        closed_issues_since_tag = []
        for issue in closed_issues:
            logger.info(issue)
            if dateutil.parser.parse(issue["closed_at"]) > dateutil.parser.parse(
                    last_tagged_release_date
            ):
                closed_issues_since_tag.append(
                    {"closed_at": issue["closed_at"], "title": issue["title"]}
                )

        return closed_issues_since_tag

    def get_version(self, cli_args: dict) -> str:
        if 'version' in cli_args:
            return cli_args['version']
        default_version = "0.0.0"
        file_path = self.file_path
        if not os.path.isfile(file_path):
            open(file_path, 'a').close()
        line = None
        with open(file_path, "r") as original_changelog:
            cur_line = 0
            while True:
                line = original_changelog.readline()
                if not line:
                    break
                cur_line += 1
        if not line:
            return default_version
        version_regex = r'^## v([0-9\.]+) - [0-9\/]+$'
        match_obj = re.match(version_regex, line)
        if match_obj:
            version = match_obj.group(1)
        version = None
        if not version:
            return default_version

        return version

    def get_next_version(self, version, types_flags, cli_args: dict) -> str:
        if 'version' in cli_args:
            return cli_args['version']
        ver = semver.VersionInfo.parse(version)
        for type in self.minor_types:
            if type in types_flags:
                return ver.bump_minor()
        for type in self.patch_types:
            if type in types_flags:
                return ver.pump_patch()

        return ""