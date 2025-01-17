import datetime
import iso8601
import logging
import requests
import rfc3339
import sys
import re
from dateutil import parser
from urllib.parse import quote

logger = logging.getLogger(__name__)


def get_date_object(date_string):
    return iso8601.parse_date(date_string)


def get_date_string(date_object):
    return rfc3339.rfc3339(date_object)


def get_last_commit_date(cli_args: dict) -> str:
    """
    Queries a specified GitLab API and returns the date of the most
    recent commit.
    """
    request_url = f"{cli_args['ip_address']}/api/v{cli_args['api_version']}/projects/" f"{cli_args['project']}/repository/branches/{quote(cli_args['branch_one'], safe='')}"
    logger.info(f"Requesting last commit date with URL: {request_url} {cli_args['token']} {cli_args['ssl']}")
    try:
        response = requests.get(
            request_url,
            headers={
                "Private-Token": cli_args["token"]
                if "token" in cli_args
                else None
            },
            verify=cli_args["ssl"],
        )
        logger.info(response.status_code)
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        logger.error(
            f"{get_last_commit_date.__name__} call to GitLab API failed with HTTPError: {ex}"
        )
        sys.exit(1)
    except requests.exceptions.ConnectionError as ex:
        logger.error(
            f"{get_last_commit_date.__name__} call to GitLab API failed with ConnectionError: {ex}"
        )
        sys.exit(1)

    logger.debug(response.status_code)
    logger.debug(response.json())

    response_json = response.json()
    commit_dict = response_json["commit"]

    logger.info(f"response")
    commit_date = get_date_object(commit_dict["committed_date"]) + datetime.timedelta(seconds=1)

    return get_date_string(commit_date)


def get_closed_issues_for_project(cli_args: dict) -> dict:
    """
    Queries a specified GitLab API and returns a list containing
    the titles and URLs of closed issues since a given date.
    """
    request_url = f"{cli_args['ip_address']}/api/v{cli_args['api_version']}/projects/{cli_args['project']}/issues?state=closed"
    logger.info(
        f"Requesting tags for project {cli_args['project']} with URL: {request_url}"
    )
    try:
        response = requests.get(
            request_url,
            headers={"PRIVATE-TOKEN": cli_args["token"]}
            if "token" in cli_args
            else None,
            verify=cli_args["ssl"],
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        logger.error(
            f"{get_commits_since_date.__name__} call to GitLab API failed with HTTPError: {ex}"
        )
        sys.exit(1)
    except requests.exceptions.ConnectionError as ex:
        logger.error(
            f"{get_commits_since_date.__name__} call to GitLab API failed with ConnectionError: {ex}"
        )
        sys.exit(1)

    logger.debug(response.status_code)
    logger.debug(response.json())

    return response.json()


def get_last_tagged_release_date(cli_args: dict) -> str:
    """
    Queries a specified GitLab API and returns a string containing
    the created_at date of the last tagged release.
    """
    request_url = f"{cli_args['ip_address']}/api/v{cli_args['api_version']}/projects/{cli_args['project']}/repository/tags"
    logger.info(
        f"Requesting tags for project {cli_args['project']} with URL: {request_url}"
    )
    try:
        response = requests.get(
            request_url,
            headers={"PRIVATE-TOKEN": cli_args["token"]}
            if "token" in cli_args
            else None,
            verify=cli_args["ssl"],
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        logger.error(
            f"{get_commits_since_date.__name__} call to GitLab API failed with HTTPError: {ex}"
        )
        sys.exit(1)
    except requests.exceptions.ConnectionError as ex:
        logger.error(
            f"{get_commits_since_date.__name__} call to GitLab API failed with ConnectionError: {ex}"
        )
        sys.exit(1)

    logger.debug(response.status_code)
    logger.debug(response.json())

    return response.json()[0]["commit"]["created_at"]


def get_commits_since_date(date: str, cli_args: dict) -> list:
    """
    Queries a specified GitLab API and returns a JSON response containing
    all commits since a given date.
    """

    clean_response = []
    done = False
    until_date = None
    while not done:
        request_url = f"{cli_args['ip_address']}/api/v{cli_args['api_version']}/projects/{cli_args['project']}" \
                      f"/repository/commits/?ref_name={cli_args['branch_two']}&since={quote(date)}"
        if until_date:
            request_url += f"&until={quote(until_date)}"
        logger.info(
            f"Requesting commits on branch '{cli_args['branch_two']}' in repository '{cli_args['project']}'"
            f" since date '{date}' with URL: {request_url}"
        )
        try:
            response = requests.get(
                request_url,
                headers={"PRIVATE-TOKEN": cli_args["token"]}
                if "token" in cli_args
                else None,
                verify=cli_args["ssl"],
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            logger.error(
                f"{get_commits_since_date.__name__} call to GitLab API failed with HTTPError: {ex}"
            )
            sys.exit(1)
        except requests.exceptions.ConnectionError as ex:
            logger.error(
                f"{get_commits_since_date.__name__} call to GitLab API failed with ConnectionError: {ex}"
            )
            sys.exit(1)

        logger.debug(response.status_code)
        logger.debug(response.json())

        response_json = response.json()
        if not response_json or (clean_response and response_json[-1]["id"] == clean_response[-1]["id"]):
            break
        until_date = response_json[-1]["created_at"]
        until_date = get_date_object(until_date) - datetime.timedelta(milliseconds=1)
        until_date = get_date_string(until_date)
        clean_response = clean_response + response_json


    return sorted(
        clean_response,
        key=lambda x: datetime.datetime.strftime(
            parser.parse(x["committed_date"]), "%Y-%m-%dT%H:%M:%S.%f"
        ),
        reverse=True,
    )


def get_commits_until_latest_bump(cli_args: dict) -> list:
    """
    Queries a specified GitLab API and returns a JSON response containing
    all commits since a given date.
    """

    clean_response = []
    until_date = None
    existed_commits = {}
    while True:
        request_url = f"{cli_args['ip_address']}/api/v{cli_args['api_version']}/projects/{cli_args['project']}" \
                      f"/repository/commits/?ref_name={cli_args['branch']}"
        if until_date:
            request_url += f"&until={until_date}"
        logger.info(
            f"Requesting commits on branch in repository '{cli_args['project']}'"
            f" with URL: {request_url}"
        )
        try:
            response = requests.get(
                request_url,
                headers={"PRIVATE-TOKEN": cli_args["token"]}
                if "token" in cli_args
                else None,
                verify=cli_args["ssl"],
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            logger.error(
                f"{get_commits_since_date.__name__} call to GitLab API failed with HTTPError: {ex}"
            )
            sys.exit(1)
        except requests.exceptions.ConnectionError as ex:
            logger.error(
                f"{get_commits_since_date.__name__} call to GitLab API failed with ConnectionError: {ex}"
            )
            sys.exit(1)

        logger.debug(response.status_code)
        logger.debug(response.json())

        response_json = response.json()
        if not response_json or (clean_response and response_json[-1]["id"] == clean_response[-1]["id"]):
            break
        bump_found = False
        for item in response_json:
            title = item['title']
            if re.match(r'^bump:.+$', title):
                bump_found = True
                break
            if item['short_id'] in existed_commits:
                continue
            existed_commits[item['short_id']] = True
            clean_response.append(item)
        if bump_found:
            break
        until_date = response_json[-1]["created_at"]
        until_date = get_date_object(until_date) - datetime.timedelta(milliseconds=1)
        until_date = get_date_string(until_date)

    return sorted(
        clean_response,
        key=lambda x: datetime.datetime.strftime(
            parser.parse(x["committed_date"]), "%Y-%m-%dT%H:%M:%S.%f"
        ),
    )
