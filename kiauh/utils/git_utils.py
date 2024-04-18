import json
import urllib.request
from http.client import HTTPResponse
from json import JSONDecodeError
from subprocess import CalledProcessError, PIPE, run
from typing import List, Type

from core.instance_manager.base_instance import BaseInstance
from core.instance_manager.instance_manager import InstanceManager
from utils.input_utils import get_number_input, get_confirm
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


def rollback_repository(repo_dir: str, instance: Type[BaseInstance]) -> None:
    q1 = "How many commits do you want to roll back"
    amount = get_number_input(q1, 1, allow_go_back=True)

    im = InstanceManager(instance)

    Logger.print_warn("Do not continue if you have ongoing prints!", start="\n")
    Logger.print_warn(
        f"All currently running {im.instance_type.__name__} services will be stopped!"
    )
    if not get_confirm(
        f"Roll back {amount} commit{'s' if amount > 1 else ''}",
        default_choice=False,
        allow_go_back=True,
    ):
        Logger.print_info("Aborting roll back ...")
        return

    im.stop_all_instance()

    try:
        cmd = ["git", "reset", "--hard", f"HEAD~{amount}"]
        run(cmd, cwd=repo_dir, check=True, stdout=PIPE, stderr=PIPE)
        Logger.print_ok(f"Rolled back {amount} commits!", start="\n")
    except CalledProcessError as e:
        Logger.print_error(f"An error occured during repo rollback:\n{e}")

    im.start_all_instance()
