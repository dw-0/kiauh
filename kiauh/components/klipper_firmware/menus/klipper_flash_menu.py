# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
import time
from typing import Type, Optional

from components.klipper_firmware.flash_options import (
    FlashOptions,
    FlashMethod,
    FlashCommand,
    ConnectionType,
)
from components.klipper_firmware.firmware_utils import (
    find_usb_device_by_id,
    find_uart_device,
    find_usb_dfu_device,
    get_sd_flash_board_list,
    start_flash_process,
    find_firmware_file,
)
from components.klipper_firmware.menus.klipper_flash_error_menu import (
    KlipperNoBoardTypesErrorMenu,
    KlipperNoFirmwareErrorMenu,
)
from components.klipper_firmware.menus.klipper_flash_help_menu import (
    KlipperMcuConnectionHelpMenu,
    KlipperFlashCommandHelpMenu,
    KlipperFlashMethodHelpMenu,
)
from core.menus import FooterType, Option

from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_CYAN, RESET_FORMAT, COLOR_YELLOW, COLOR_RED
from utils.input_utils import get_number_input
from utils.logger import Logger


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashMethodMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.help_menu = KlipperFlashMethodHelpMenu
        self.input_label_txt = "Select flash method"
        self.footer_type = FooterType.BACK_HELP
        self.flash_options = FlashOptions()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(self.select_regular, menu=False),
            "2": Option(self.select_sdcard, menu=False),
        }

    def print_menu(self) -> None:
        header = " [ MCU Flash Menu ] "
        subheader = f"{COLOR_YELLOW}ATTENTION:{RESET_FORMAT}"
        subline1 = f"{COLOR_YELLOW}Make sure to select the correct method for the  MCU!{RESET_FORMAT}"
        subline2 = f"{COLOR_YELLOW}Not all MCUs support both methods!{RESET_FORMAT}"

        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Select the flash method for flashing the MCU.         |
            |                                                       |
            | {subheader:<62} |
            | {subline1:<62} |
            | {subline2:<62} |
            |-------------------------------------------------------|
            |                                                       |
            | 1) Regular flashing method                            |
            | 2) Updating via SD-Card Update                        |
            |                                                       |
            """
        )[1:]
        print(menu, end="")

    def select_regular(self, **kwargs):
        self.flash_options.flash_method = FlashMethod.REGULAR
        self.goto_next_menu()

    def select_sdcard(self, **kwargs):
        self.flash_options.flash_method = FlashMethod.SD_CARD
        self.goto_next_menu()

    def goto_next_menu(self, **kwargs):
        if find_firmware_file(self.flash_options.flash_method):
            KlipperFlashCommandMenu(previous_menu=self.__class__).run()
        else:
            KlipperNoFirmwareErrorMenu().run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashCommandMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.help_menu = KlipperFlashCommandHelpMenu
        self.input_label_txt = "Select flash command"
        self.footer_type = FooterType.BACK_HELP
        self.flash_options = FlashOptions()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else KlipperFlashMethodMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(self.select_flash, menu=False),
            "2": Option(self.select_serialflash, menu=False),
        }
        self.default_option = Option(self.select_flash, menu=False)

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            /=======================================================\\
            |                                                       |
            | Which flash command to use for flashing the MCU?      |
            | 1) make flash (default)                               |
            | 2) make serialflash (stm32flash)                      |
            |                                                       |
            """
        )[1:]
        print(menu, end="")

    def select_flash(self, **kwargs):
        self.flash_options.flash_command = FlashCommand.FLASH
        self.goto_next_menu()

    def select_serialflash(self, **kwargs):
        self.flash_options.flash_command = FlashCommand.SERIAL_FLASH
        self.goto_next_menu()

    def goto_next_menu(self, **kwargs):
        KlipperSelectMcuConnectionMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectMcuConnectionMenu(BaseMenu):
    def __init__(
        self, previous_menu: Optional[Type[BaseMenu]] = None, standalone: bool = False
    ):
        super().__init__()
        self.__standalone = standalone
        self.help_menu = KlipperMcuConnectionHelpMenu
        self.input_label_txt = "Select connection type"
        self.footer_type = FooterType.BACK_HELP
        self.flash_options = FlashOptions()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else KlipperFlashCommandMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.select_usb, menu=False),
            "2": Option(method=self.select_dfu, menu=False),
            "3": Option(method=self.select_usb_dfu, menu=False),
        }

    def print_menu(self) -> None:
        header = "Make sure that the controller board is connected now!"
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            |                                                       |
            | How is the controller board connected to the host?    |
            | 1) USB                                                |
            | 2) UART                                               |
            | 3) USB (DFU mode)                                     |
            |                                                       |
            """
        )[1:]
        print(menu, end="")

    def select_usb(self, **kwargs):
        self.flash_options.connection_type = ConnectionType.USB
        self.get_mcu_list()

    def select_dfu(self, **kwargs):
        self.flash_options.connection_type = ConnectionType.UART
        self.get_mcu_list()

    def select_usb_dfu(self, **kwargs):
        self.flash_options.connection_type = ConnectionType.USB_DFU
        self.get_mcu_list()

    def get_mcu_list(self, **kwargs):
        conn_type = self.flash_options.connection_type

        if conn_type is ConnectionType.USB:
            Logger.print_status("Identifying MCU connected via USB ...")
            self.flash_options.mcu_list = find_usb_device_by_id()
        elif conn_type is ConnectionType.UART:
            Logger.print_status("Identifying MCU possibly connected via UART ...")
            self.flash_options.mcu_list = find_uart_device()
        elif conn_type is ConnectionType.USB_DFU:
            Logger.print_status("Identifying MCU connected via USB in DFU mode ...")
            self.flash_options.mcu_list = find_usb_dfu_device()

        if len(self.flash_options.mcu_list) < 1:
            Logger.print_warn("No MCUs found!")
            Logger.print_warn("Make sure they are connected and repeat this step.")

        # if standalone is True, we only display the MCUs to the user and return
        if self.__standalone and len(self.flash_options.mcu_list) > 0:
            Logger.print_ok("The following MCUs were found:", prefix=False)
            for i, mcu in enumerate(self.flash_options.mcu_list):
                print(f"   ● MCU #{i}: {COLOR_CYAN}{mcu}{RESET_FORMAT}")
            time.sleep(3)
            return

        self.goto_next_menu()

    def goto_next_menu(self, **kwargs):
        KlipperSelectMcuIdMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectMcuIdMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.flash_options = FlashOptions()
        self.mcu_list = self.flash_options.mcu_list
        self.input_label_txt = "Select MCU to flash"
        self.footer_type = FooterType.BACK_HELP

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        self.previous_menu: Type[BaseMenu] = (
            previous_menu
            if previous_menu is not None
            else KlipperSelectMcuConnectionMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{i}": Option(self.flash_mcu, False, f"{i}")
            for i in range(len(self.mcu_list))
        }

    def print_menu(self) -> None:
        header = "!!! ATTENTION !!!"
        header2 = f"[{COLOR_CYAN}List of available MCUs{RESET_FORMAT}]"
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Make sure, to select the correct MCU!                 |
            | ONLY flash a firmware created for the respective MCU! |
            |                                                       |
            |{header2:-^64}|
            
            """
        )[1:]

        for i, mcu in enumerate(self.mcu_list):
            mcu = mcu.split("/")[-1]
            menu += f"   ● MCU #{i}: {COLOR_CYAN}{mcu}{RESET_FORMAT}\n"

        print(menu, end="\n")

    def flash_mcu(self, **kwargs):
        index = int(kwargs.get("opt_index"))
        selected_mcu = self.mcu_list[index]
        self.flash_options.selected_mcu = selected_mcu

        if self.flash_options.flash_method == FlashMethod.SD_CARD:
            KlipperSelectSDFlashBoardMenu(previous_menu=self.__class__).run()
        elif self.flash_options.flash_method == FlashMethod.REGULAR:
            KlipperFlashOverviewMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectSDFlashBoardMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.flash_options = FlashOptions()
        self.available_boards = get_sd_flash_board_list()
        self.input_label_txt = "Select board type"

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else KlipperSelectMcuIdMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{i}": Option(self.board_select, False, f"{i}")
            for i in range(len(self.available_boards))
        }

    def print_menu(self) -> None:
        if len(self.available_boards) < 1:
            KlipperNoBoardTypesErrorMenu().run()
        else:
            menu = textwrap.dedent(
                """
                /=======================================================\\
                | Please select the type of board that corresponds to   |
                | the currently selected MCU ID you chose before.       |
                |                                                       |
                | The following boards are currently supported:         |
                |-------------------------------------------------------|
                """
            )[1:]

            for i, board in enumerate(self.available_boards):
                line = f" {i}) {board}"
                menu += f"|{line:<55}|\n"

            print(menu, end="")

    def board_select(self, **kwargs):
        board = int(kwargs.get("opt_index"))
        self.flash_options.selected_board = self.available_boards[board]
        self.baudrate_select()

    def baudrate_select(self, **kwargs):
        menu = textwrap.dedent(
            """
            /=======================================================\\
            | If your board is flashed with firmware that connects  |
            | at a custom baud rate, please change it now.          |
            |                                                       |
            | If you are unsure, stick to the default 250000!       |
            \\=======================================================/
            """
        )[1:]
        print(menu, end="")
        self.flash_options.selected_baudrate = get_number_input(
            question="Please set the baud rate",
            default=250000,
            min_count=0,
            allow_go_back=True,
        )
        KlipperFlashOverviewMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashOverviewMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.flash_options = FlashOptions()
        self.input_label_txt = "Perform action (default=Y)"

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        self.previous_menu: Type[BaseMenu] = previous_menu

    def set_options(self) -> None:
        self.options = {
            "Y": Option(self.execute_flash, menu=False),
            "N": Option(self.abort_process, menu=False),
        }

        self.default_option = Option(self.execute_flash, menu=False)

    def print_menu(self) -> None:
        header = "!!! ATTENTION !!!"
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)

        method = self.flash_options.flash_method.value
        command = self.flash_options.flash_command.value
        conn_type = self.flash_options.connection_type.value
        mcu = self.flash_options.selected_mcu
        board = self.flash_options.selected_board
        baudrate = self.flash_options.selected_baudrate
        subheader = f"[{COLOR_CYAN}Overview{RESET_FORMAT}]"
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Before contuining the flashing process, please check  |
            | if all parameters were set correctly! Once you made   |
            | sure everything is correct, start the process. If any |
            | parameter needs to be changed, you can go back (B)    |
            | step by step or abort and start from the beginning.   |
            |{subheader:-^64}|
            
            """
        )[1:]

        menu += f"   ● MCU: {COLOR_CYAN}{mcu}{RESET_FORMAT}\n"
        menu += f"   ● Connection: {COLOR_CYAN}{conn_type}{RESET_FORMAT}\n"
        menu += f"   ● Flash method: {COLOR_CYAN}{method}{RESET_FORMAT}\n"
        menu += f"   ● Flash command: {COLOR_CYAN}{command}{RESET_FORMAT}\n"

        if self.flash_options.flash_method is FlashMethod.SD_CARD:
            menu += f"   ● Board type: {COLOR_CYAN}{board}{RESET_FORMAT}\n"
            menu += f"   ● Baudrate: {COLOR_CYAN}{baudrate}{RESET_FORMAT}\n"

        menu += textwrap.dedent(
            """
            |-------------------------------------------------------|
            |  Y) Start flash process                               |
            |  N) Abort - Return to Advanced Menu                   |
            """
        )
        print(menu, end="")

    def execute_flash(self, **kwargs):
        from core.menus.advanced_menu import AdvancedMenu

        start_flash_process(self.flash_options)
        Logger.print_info("Returning to MCU Flash Menu in 5 seconds ...")
        time.sleep(5)
        KlipperFlashMethodMenu(previous_menu=AdvancedMenu).run()

    def abort_process(self, **kwargs):
        from core.menus.advanced_menu import AdvancedMenu

        AdvancedMenu().run()
