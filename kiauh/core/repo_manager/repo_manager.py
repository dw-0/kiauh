#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
import subprocess
from pathlib import Path

from utils.input_utils import get_confirm
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class RepoManager:
    def __init__(
        self,
        repo: str,
        target_dir: str,
        branch: str = None,
    ):
        self._repo = repo
        self._branch = branch if branch is not None else "master"
        self._method = self._get_method()
        self._target_dir = target_dir

    @property
    def repo(self) -> str:
        return self._repo

    @repo.setter
    def repo(self, value) -> None:
        self._repo = value

    @property
    def branch(self) -> str:
        return self._branch

    @branch.setter
    def branch(self, value) -> None:
        self._branch = value

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, value) -> None:
        self._method = value

    @property
    def target_dir(self) -> str:
        return self._target_dir

    @target_dir.setter
    def target_dir(self, value) -> None:
        self._target_dir = value

    @staticmethod
    def get_repo_name(repo: Path) -> str:
        """
        Helper method to extract the organisation and name of a repository |
        :param repo: repository to extract the values from
        :return: String in form of "<orga>/<name>"
        """
        if not repo.exists() and not repo.joinpath(".git").exists():
            return "-"

        try:
            cmd = ["git", "-C", repo, "config", "--get", "remote.origin.url"]
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            return "/".join(result.decode().strip().split("/")[-2:])
        except subprocess.CalledProcessError:
            return "-"

    @staticmethod
    def get_local_commit(repo: Path) -> str:
        if not repo.exists() and not repo.joinpath(".git").exists():
            return "-"

        try:
            cmd = f"cd {repo} && git describe HEAD --always --tags | cut -d '-' -f 1,2"
            return subprocess.check_output(cmd, shell=True, text=True).strip()
        except subprocess.CalledProcessError:
            return "-"

    @staticmethod
    def get_remote_commit(repo: Path) -> str:
        if not repo.exists() and not repo.joinpath(".git").exists():
            return "-"

        try:
            # get locally checked out branch
            branch_cmd = f"cd {repo} && git branch | grep -E '\*'"
            branch = subprocess.check_output(branch_cmd, shell=True, text=True)
            branch = branch.split("*")[-1].strip()
            cmd = f"cd {repo} && git describe 'origin/{branch}' --always --tags | cut -d '-' -f 1,2"
            return subprocess.check_output(cmd, shell=True, text=True).strip()
        except subprocess.CalledProcessError:
            return "-"

    def clone_repo(self):
        log = f"Cloning repository from '{self.repo}' with method '{self.method}'"
        Logger.print_status(log)
        try:
            if Path(self.target_dir).exists():
                question = f"'{self.target_dir}' already exists. Overwrite?"
                if not get_confirm(question, default_choice=False):
                    Logger.print_info("Skipping re-clone of repository.")
                    return
                shutil.rmtree(self.target_dir)

            self._clone()
            self._checkout()
        except subprocess.CalledProcessError:
            log = "An unexpected error occured during cloning of the repository."
            Logger.print_error(log)
            return
        except OSError as e:
            Logger.print_error(f"Error removing existing repository: {e.strerror}")
            return

    def pull_repo(self) -> None:
        Logger.print_status(f"Updating repository '{self.repo}' ...")
        try:
            self._pull()
        except subprocess.CalledProcessError:
            log = "An unexpected error occured during updating the repository."
            Logger.print_error(log)
            return

    def _clone(self):
        try:
            command = ["git", "clone", self.repo, self.target_dir]
            subprocess.run(command, check=True)

            Logger.print_ok("Clone successful!")
        except subprocess.CalledProcessError as e:
            log = f"Error cloning repository {self.repo}: {e.stderr.decode()}"
            Logger.print_error(log)
            raise

    def _checkout(self):
        try:
            command = ["git", "checkout", f"{self.branch}"]
            subprocess.run(command, cwd=self.target_dir, check=True)

            Logger.print_ok("Checkout successful!")
        except subprocess.CalledProcessError as e:
            log = f"Error checking out branch {self.branch}: {e.stderr.decode()}"
            Logger.print_error(log)
            raise

    def _pull(self) -> None:
        try:
            command = ["git", "pull"]
            subprocess.run(command, cwd=self.target_dir, check=True)
        except subprocess.CalledProcessError as e:
            log = f"Error on git pull: {e.stderr.decode()}"
            Logger.print_error(log)
            raise

    def _get_method(self) -> str:
        return "ssh" if self.repo.startswith("git") else "https"
