from argparse import ArgumentParser
from .zpm_generator import ZPMGenerator
from .zpw_generator import ZPWGenerator

from changelog_generator.generator import generate_changelog

systems = {
    "zpm": ZPMGenerator,
    "zpw": ZPWGenerator,
}

def process_arguments() -> dict:
    parser = ArgumentParser(prog="changegen")
    parser.add_argument(
        "-sy",
        "--system",
        dest="system",
        help="specify system, available options: zpm, zpw",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--ip",
        dest="ip",
        help="specify IP address of GitLab repository - should include \
              protocol (http/s)",
        required=True,
    )
    parser.add_argument(
        "-a",
        "--api",
        dest="api",
        help="specify GitLab API version",
        choices=["1", "2", "3", "4"],
        default="4",
    )
    # parser.add_argument(
    #     dest="group",
    #     help="specify GitLab group",
    #     required=True,
    # )
    parser.add_argument(
        "-p",
        "--project",
        dest="project",
        help="specify GitLab project",
        required=True,
    )
    parser.add_argument(
        "-b",
        "--branch",
        dest="branch",
        help="specify GitLab branches to compare",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        help="specify version number",
    )
    parser.add_argument(
        "-t",
        "--token",
        dest="token",
        help="gitlab personal token for auth",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--ssl",
        dest="ssl",
        help="specify whether or not to enable certificate verification",
        required=False,
        default=True,
        type=lambda x: (str(x).lower() not in ["false", "2", "no"]),
    )
    parser.add_argument(
        "-sp",
        "--subproject",
        dest="sub_project",
        help="specify project to filter",
    )

    args = parser.parse_args()

    return {
        "system": args.system,
        "ip_address": args.ip,
        "api_version": args.api,
        # "project_group": args.group,
        "project": args.project,
        "sub_project": args.sub_project,
        "branch": args.branch,
        "version": args.version,
        "token": args.token,
        "ssl": args.ssl,
    }


def main():
    cli_args = process_arguments()
    generator = None
    generator = systems[cli_args['system']]()
    if not generator:
        return
    generator.generate_changelog(cli_args)


if __name__ == "__main__":
    main()
