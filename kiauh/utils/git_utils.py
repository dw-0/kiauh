from __future__ import annotations

import json
import shutil
import urllib.request
from http.client import HTTPResponse
from json import JSONDecodeError
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, check_output, run
from typing import List, Type

from core.instance_manager.instance_manager import InstanceManager
from core.instance_type import InstanceType
from core.logger import Logger
from utils.input_utils import get_confirm, get_number_input
from utils.instance_utils import get_instances


class GitException(Exception):
    pass


def git_clone_wrapper(
    repo: str, target_dir: Path, branch: str | None = None, force: bool = False
) -> None:
    """
    Clones a repository from the given URL and checks out the specified branch if given.

    :param repo: The URL of the repository to clone.
    :param branch: The branch to check out. If None, the default branch will be checked out.
    :param target_dir: The directory where the repository will be cloned.
    :param force: Force the cloning of the repository even if it already exists.
    :return: None
    """
    log = f"Cloning repository from '{repo}'"
    Logger.print_status(log)
    try:
        if Path(target_dir).exists():
            question = f"'{target_dir}' already exists. Overwrite?"
            if not force and not get_confirm(question, default_choice=False):
                Logger.print_info("Skip cloning of repository ...")
                return
            shutil.rmtree(target_dir)

        git_cmd_clone(repo, target_dir)
        git_cmd_checkout(branch, target_dir)
    except CalledProcessError:
        log = "An unexpected error occured during cloning of the repository."
        Logger.print_error(log)
        raise GitException(log)
    except OSError as e:
        Logger.print_error(f"Error removing existing repository: {e.strerror}")
        raise GitException(f"Error removing existing repository: {e.strerror}")


def git_pull_wrapper(repo: str, target_dir: Path) -> None:
    """
    A function that updates a repository using git pull.

    :param repo: The repository to update.
    :param target_dir: The directory of the repository.
    :return: None
    """
    Logger.print_status(f"Updating repository '{repo}' ...")
    try:
        git_cmd_pull(target_dir)
    except CalledProcessError:
        log = "An unexpected error occured during updating the repository."
        Logger.print_error(log)
        return


def get_repo_name(repo: Path) -> tuple[str, str] | None:
    """
    Helper method to extract the organisation and name of a repository |
    :param repo: repository to extract the values from
    :return: String in form of "<orga>/<name>" or None
    """
    if not repo.exists() or not repo.joinpath(".git").exists():
        return "-", "-"

    try:
        cmd = ["git", "-C", repo.as_posix(), "config", "--get", "remote.origin.url"]
        result: str = check_output(cmd, stderr=DEVNULL).decode(encoding="utf-8")
        substrings: List[str] = result.strip().split("/")[-2:]
        return substrings[0], substrings[1]

        # return "/".join(substrings).replace(".git", "")
    except CalledProcessError:
        return None


def get_local_tags(repo_path: Path, _filter: str | None = None) -> List[str]:
    """
    Get all tags of a local Git repository
    :param repo_path: Path to the local Git repository
    :param _filter: Optional filter to filter the tags by
    :return: List of tags
    """
    try:
        cmd = ["git", "tag", "-l"]

        if _filter is not None:
            cmd.append(f"'${_filter}'")

        result: str = check_output(
            cmd,
            stderr=DEVNULL,
            cwd=repo_path.as_posix(),
        ).decode(encoding="utf-8")

        tags = result.split("\n")
        return tags[:-1]

    except CalledProcessError:
        return []


def get_remote_tags(repo_path: str) -> List[str]:
    """
    Gets the tags of a GitHub repostiory
    :param repo_path: path of the GitHub repository - e.g. `<owner>/<name>`
    :return: List of tags
    """
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


def get_latest_remote_tag(repo_path: str) -> str:
    """
    Gets the latest stable tag of a GitHub repostiory
    :param repo_path: path of the GitHub repository - e.g. `<owner>/<name>`
    :return: tag or empty string
    """
    try:
        if len(latest_tag := get_remote_tags(repo_path)) > 0:
            return latest_tag[0]
        else:
            return ""
    except Exception:
        raise


def get_latest_unstable_tag(repo_path: str) -> str:
    """
    Gets the latest unstable (alpha, beta, rc) tag of a GitHub repository
    :param repo_path: path of the GitHub repository - e.g. `<owner>/<name>`
    :return: tag or empty string
    """
    try:
        if (
            len(unstable_tags := [t for t in get_remote_tags(repo_path) if "-" in t])
            > 0
        ):
            return unstable_tags[0]
        else:
            return ""
    except Exception:
        Logger.print_error("Error while getting the latest unstable tag")
        raise


def compare_semver_tags(tag1: str, tag2: str) -> bool:
    """
    Compare two semver version strings.
    Does not support comparing pre-release versions (e.g. 1.0.0-rc.1, 1.0.0-beta.1)
    :param tag1: First version string
    :param tag2: Second version string
    :return: True if tag1 is greater than tag2, False otherwise
    """
    if tag1 == tag2:
        return False

    def parse_version(v):
        return list(map(int, v[1:].split(".")))

    tag1_parts = parse_version(tag1)
    tag2_parts = parse_version(tag2)

    max_len = max(len(tag1_parts), len(tag2_parts))
    tag1_parts += [0] * (max_len - len(tag1_parts))
    tag2_parts += [0] * (max_len - len(tag2_parts))

    for part1, part2 in zip(tag1_parts, tag2_parts):
        if part1 != part2:
            return part1 > part2

    return False


def get_local_commit(repo: Path) -> str | None:
    if not repo.exists() or not repo.joinpath(".git").exists():
        return None

    try:
        cmd = f"cd {repo} && git describe HEAD --always --tags | cut -d '-' -f 1,2"
        return check_output(cmd, shell=True, text=True).strip()
    except CalledProcessError:
        return None


def get_remote_commit(repo: Path) -> str | None:
    if not repo.exists() or not repo.joinpath(".git").exists():
        return None

    try:
        # get locally checked out branch
        branch_cmd = f"cd {repo} && git branch | grep -E '\*'"
        branch = check_output(branch_cmd, shell=True, text=True)
        branch = branch.split("*")[-1].strip()
        cmd = f"cd {repo} && git describe 'origin/{branch}' --always --tags | cut -d '-' -f 1,2"
        return check_output(cmd, shell=True, text=True).strip()
    except CalledProcessError:
        return None


def git_cmd_clone(repo: str, target_dir: Path) -> None:
    try:
        command = ["git", "clone", repo, target_dir.as_posix()]
        run(command, check=True)

        Logger.print_ok("Clone successful!")
    except CalledProcessError as e:
        error = e.stderr.decode() if e.stderr else "Unknown error"
        log = f"Error cloning repository {repo}: {error}"
        Logger.print_error(log)
        raise


def git_cmd_checkout(branch: str | None, target_dir: Path) -> None:
    if branch is None:
        return

    try:
        command = ["git", "checkout", f"{branch}"]
        run(command, cwd=target_dir, check=True)

        Logger.print_ok("Checkout successful!")
    except CalledProcessError as e:
        log = f"Error checking out branch {branch}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def git_cmd_pull(target_dir: Path) -> None:
    try:
        command = ["git", "pull"]
        run(command, cwd=target_dir, check=True)
    except CalledProcessError as e:
        log = f"Error on git pull: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def rollback_repository(repo_dir: Path, instance: Type[InstanceType]) -> None:
    q1 = "How many commits do you want to roll back"
    amount = get_number_input(q1, 1, allow_go_back=True)

    instances = get_instances(instance)

    Logger.print_warn("Do not continue if you have ongoing prints!", start="\n")
    Logger.print_warn(
        f"All currently running {instance.__name__} services will be stopped!"
    )
    if not get_confirm(
        f"Roll back {amount} commit{'s' if amount > 1 else ''}",
        default_choice=False,
        allow_go_back=True,
    ):
        Logger.print_info("Aborting roll back ...")
        return

    InstanceManager.stop_all(instances)

    try:
        cmd = ["git", "reset", "--hard", f"HEAD~{amount}"]
        run(cmd, cwd=repo_dir, check=True, stdout=PIPE, stderr=PIPE)
        Logger.print_ok(f"Rolled back {amount} commits!", start="\n")
    except CalledProcessError as e:
        Logger.print_error(f"An error occured during repo rollback:\n{e}")

    InstanceManager.start_all(instances)
