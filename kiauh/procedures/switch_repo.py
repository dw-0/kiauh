# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

from components.klipper import (
    KLIPPER_BACKUP_DIR,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_REQ_FILE,
)
from components.klipper.klipper import Klipper
from components.klipper.klipper_utils import install_klipper_packages
from components.moonraker import (
    MOONRAKER_BACKUP_DIR,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_REQ_FILE,
)
from components.moonraker.moonraker import Moonraker
from components.moonraker.services.moonraker_setup_service import (
    install_moonraker_packages,
)
from core.backup_manager.backup_manager import BackupManager, BackupManagerException
from core.instance_manager.instance_manager import InstanceManager
from core.logger import Logger
from utils.git_utils import GitException, get_repo_name, git_clone_wrapper
from utils.instance_utils import get_instances
from utils.sys_utils import (
    VenvCreationFailedException,
    create_python_venv,
    install_python_requirements,
)


class RepoSwitchFailedException(Exception):
    pass


def run_switch_repo_routine(
    name: Literal["klipper", "moonraker"], repo_url: str, branch: str
) -> None:
    repo_dir: Path = KLIPPER_DIR if name == "klipper" else MOONRAKER_DIR
    env_dir: Path = KLIPPER_ENV_DIR if name == "klipper" else MOONRAKER_ENV_DIR
    req_file = KLIPPER_REQ_FILE if name == "klipper" else MOONRAKER_REQ_FILE
    backup_dir: Path = KLIPPER_BACKUP_DIR if name == "klipper" else MOONRAKER_BACKUP_DIR
    _type = Klipper if name == "klipper" else Moonraker

    # step 1: stop all instances
    Logger.print_status(f"Stopping all {_type.__name__} instances ...")
    instances = get_instances(_type)
    InstanceManager.stop_all(instances)

    repo_dir_backup_path: Path | None = None
    env_dir_backup_path: Path | None = None

    try:
        # step 2: backup old repo and env
        org, _ = get_repo_name(repo_dir)
        backup_dir = backup_dir.joinpath(org)
        bm = BackupManager()
        repo_dir_backup_path = bm.backup_directory(
            repo_dir.name,
            repo_dir,
            backup_dir,
        )
        env_dir_backup_path = bm.backup_directory(
            env_dir.name,
            env_dir,
            backup_dir,
        )

        if not (repo_url or branch):
            error = f"Invalid repository URL ({repo_url}) or branch ({branch})!"
            raise ValueError(error)

        # step 4: clone new repo
        git_clone_wrapper(repo_url, repo_dir, branch, force=True)

        # step 5: install os dependencies
        if name == "klipper":
            install_klipper_packages()
        elif name == "moonraker":
            install_moonraker_packages()

        # step 6: recreate python virtualenv
        Logger.print_status(f"Recreating {_type.__name__} virtualenv ...")
        if not create_python_venv(env_dir, force=True):
            raise GitException(f"Failed to recreate virtualenv for {_type.__name__}")
        else:
            install_python_requirements(env_dir, req_file)

        Logger.print_ok(f"Switched to {repo_url} at branch {branch}!")

    except BackupManagerException as e:
        Logger.print_error(f"Error during backup of repository: {e}")
        raise RepoSwitchFailedException(e)

    except (GitException, VenvCreationFailedException) as e:
        # if something goes wrong during cloning or recreating the virtualenv,
        # we restore the backup of the repo and env
        Logger.print_error(f"Error during repository switch: {e}", start="\n")
        Logger.print_status(f"Restoring last backup of {_type.__name__} ...")
        _restore_repo_backup(
            _type.__name__,
            env_dir,
            env_dir_backup_path,
            repo_dir,
            repo_dir_backup_path,
        )

    except RepoSwitchFailedException as e:
        Logger.print_error(f"Something went wrong: {e}")
        return

    Logger.print_status(f"Restarting all {_type.__name__} instances ...")
    InstanceManager.start_all(instances)


def _restore_repo_backup(
    name: str,
    env_dir: Path,
    env_dir_backup_path: Path | None,
    repo_dir: Path,
    repo_dir_backup_path: Path | None,
) -> None:
    # if repo_dir_backup_path is not None and env_dir_backup_path is not None:
    if not repo_dir_backup_path or not env_dir_backup_path:
        raise RepoSwitchFailedException(
            f"Unable to restore backup of {name}! Path of backups directory is None!"
        )

    try:
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
            shutil.copytree(repo_dir_backup_path, repo_dir)
        if env_dir.exists():
            shutil.rmtree(env_dir)
            shutil.copytree(env_dir_backup_path, env_dir)
        Logger.print_warn(f"Restored backup of {name} successfully!")
    except Exception as e:
        raise RepoSwitchFailedException(f"Error restoring backup: {e}")
