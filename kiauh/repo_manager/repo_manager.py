#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
import subprocess

from kiauh.utils.input_utils import get_confirm
from kiauh.utils.logger import Logger


# noinspection PyMethodMayBeStatic
class RepoManager:
    def __init__(self, repo: str, branch: str, target_dir: str):
        self._repo = repo
        self._branch = branch
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

    def clone_repo(self):
        log = f"Cloning repository from '{self.repo}' with method '{self.method}'"
        Logger.print_info(log)
        try:
            if os.path.exists(self.target_dir):
                if not get_confirm("Target directory already exists. Overwrite?"):
                    Logger.print_info("Skipping re-clone of repository ...")
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

    def _clone(self):
        try:
            command = ["git", "clone", self.repo, self.target_dir]
            subprocess.run(command, check=True)

            Logger.print_ok("Clone successfull!")
        except subprocess.CalledProcessError as e:
            log = f"Error cloning repository {self.repo}: {e.stderr.decode()}"
            Logger.print_error(log)
            raise

    def _checkout(self):
        try:
            command = ["git", "checkout", f"{self.branch}"]
            subprocess.run(command, cwd=self.target_dir, check=True)

            Logger.print_ok("Checkout successfull!")
        except subprocess.CalledProcessError as e:
            log = f"Error checking out branch {self.branch}: {e.stderr.decode()}"
            Logger.print_error(log)
            raise

    def _get_method(self) -> str:
        return "ssh" if self.repo.startswith("git") else "https"
