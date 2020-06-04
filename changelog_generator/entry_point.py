from argparse import ArgumentParser

from changelog_generator.generator import generate_changelog


def process_arguments() -> dict:
    parser = ArgumentParser(prog="changegen")
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
        "--branches",
        nargs=2,
        dest="branches",
        help="specify GitLab branches to compare",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        help="specify version number",
        required=True,
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
        required=True,
    )

    args = parser.parse_args()

    return {
        "ip_address": args.ip,
        "api_version": args.api,
        # "project_group": args.group,
        "project": args.project,
        "sub_project": args.sub_project,
        "branch_one": args.branches[0],
        "branch_two": args.branches[1],
        "version": args.version,
        "token": args.token,
        "ssl": args.ssl,
    }


def main():
    generate_changelog(process_arguments())


if __name__ == "__main__":
    main()
