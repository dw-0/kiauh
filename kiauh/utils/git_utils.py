import json
import urllib.request
from http.client import HTTPResponse
from json import JSONDecodeError
from typing import List

from utils.logger import Logger


def get_tags(repo_path: str) -> List[str]:
    try:
        url = f"https://api.github.com/repos/{repo_path}/tags"
        with urllib.request.urlopen(url) as r:
            response: HTTPResponse = r
            if response.getcode() != 200:
                Logger.print_error(
                    f"Error retrieving tags: HTTP status code {response.getcode()}"
                )
                return []

            data = json.loads(response.read())
            return [item["name"] for item in data]
    except (JSONDecodeError, TypeError) as e:
        Logger.print_error(f"Error while processing the response: {e}")
        raise


def get_latest_tag(repo_path: str) -> str:
    """
    Gets the latest stable tag of a GitHub repostiory
    :param repo_path: path of the GitHub repository - e.g. `<owner>/<name>`
    :return: tag or empty string
    """
    try:
        if len(latest_tag := get_tags(repo_path)) > 0:
            return latest_tag[0]
        else:
            return ""
    except Exception:
        Logger.print_error("Error while getting the latest tag")
        raise


def get_latest_unstable_tag(repo_path: str) -> str:
    """
    Gets the latest unstable (alpha, beta, rc) tag of a GitHub repository
    :param repo_path: path of the GitHub repository - e.g. `<owner>/<name>`
    :return: tag or empty string
    """
    try:
        if len(unstable_tags := [t for t in get_tags(repo_path) if "-" in t]) > 0:
            return unstable_tags[0]
        else:
            return ""
    except Exception:
        Logger.print_error("Error while getting the latest unstable tag")
        raise
