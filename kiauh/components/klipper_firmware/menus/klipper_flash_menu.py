# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
import time
from pathlib import Path
from typing import Type

from components.klipper_firmware.firmware_utils import (
    find_firmware_file,
    find_uart_device,
    find_usb_device_by_id,
    find_usb_dfu_device,
    find_usb_rp2_boot_device,
    get_sd_flash_board_list,
    start_flash_process,
)
from components.klipper_firmware.flash_options import (
    ConnectionType,
    FlashCommand,
    FlashMethod,
    FlashOptions,
)
from components.klipper_firmware.menus.klipper_flash_error_menu import (
    KlipperNoBoardTypesErrorMenu,
    KlipperNoFirmwareErrorMenu,
)
from components.klipper_firmware.menus.klipper_flash_help_menu import (
    KlipperFlashCommandHelpMenu,
    KlipperFlashMethodHelpMenu,
    KlipperMcuConnectionHelpMenu,
)
from core.logger import DialogType, Logger
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu, MenuTitleStyle
from core.types.color import Color
from utils.input_utils import get_number_input


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashMethodMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "MCU Flash Menu"
        self.title_color = Color.CYAN
        self.help_menu = KlipperFlashMethodHelpMenu
        self.input_label_txt = "Select flash method"
        self.footer_type = FooterType.BACK_HELP
        self.flash_options = FlashOptions()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(self.select_regular),
            "2": Option(self.select_sdcard),
        }

    def print_menu(self) -> None:
        subheader = Color.apply("ATTENTION:", Color.YELLOW)
        subline1 = Color.apply(
            "Make sure to select the correct method for the MCU!", Color.YELLOW
        )
        subline2 = Color.apply("Not all MCUs support both methods!", Color.YELLOW)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Select the flash method for flashing the MCU.         ║
            ║                                                       ║
            ║ {subheader:<62} ║
            ║ {subline1:<62} ║
            ║ {subline2:<62} ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Regular flashing method                            ║
            ║ 2) Updating via SD-Card Update                        ║
            ╟───────────────────────────┬───────────────────────────╢
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
        if find_firmware_file():
            KlipperFlashCommandMenu(previous_menu=self.__class__).run()
        else:
            KlipperNoFirmwareErrorMenu().run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashCommandMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "Which flash command to use for flashing the MCU?"
        self.title_style = MenuTitleStyle.PLAIN
        self.title_color = Color.YELLOW
        self.help_menu = KlipperFlashCommandHelpMenu
        self.input_label_txt = "Select flash command"
        self.footer_type = FooterType.BACK_HELP
        self.flash_options = FlashOptions()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = (
            previous_menu if previous_menu is not None else KlipperFlashMethodMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(self.select_flash),
            "2": Option(self.select_serialflash),
        }
        self.default_option = Option(self.select_flash)

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ 1) make flash (default)                               ║
            ║ 2) make serialflash (stm32flash)                      ║
            ╟───────────────────────────┬───────────────────────────╢
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
        self, previous_menu: Type[BaseMenu] | None = None, standalone: bool = False
    ):
        super().__init__()
        self.title = "Make sure that the controller board is connected now!"
        self.title_style = MenuTitleStyle.PLAIN
        self.title_color = Color.YELLOW
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.__standalone = standalone
        self.help_menu = KlipperMcuConnectionHelpMenu
        self.input_label_txt = "Select connection type"
        self.footer_type = FooterType.BACK_HELP
        self.flash_options = FlashOptions()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = (
            previous_menu if previous_menu is not None else KlipperFlashCommandMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.select_usb),
            "2": Option(method=self.select_dfu),
            "3": Option(method=self.select_usb_dfu),
            "4": Option(method=self.select_usb_rp2040),
        }

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ How is the controller board connected to the host?    ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) USB                                                ║
            ║ 2) UART                                               ║
            ║ 3) USB (DFU mode)                                     ║
            ║ 4) USB (RP2040 mode)                                  ║
            ╟───────────────────────────┬───────────────────────────╢
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

    def select_usb_rp2040(self, **kwargs):
        self.flash_options.connection_type = ConnectionType.USB_RP2040
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
        elif conn_type is ConnectionType.USB_RP2040:
            Logger.print_status(
                "Identifying MCU connected via USB in RP2 Boot mode ..."
            )
            self.flash_options.mcu_list = find_usb_rp2_boot_device()

        if len(self.flash_options.mcu_list) < 1:
            Logger.print_warn("No MCUs found!")
            Logger.print_warn("Make sure they are connected and repeat this step.")
            time.sleep(3)
            return

        # if standalone is True, we only display the MCUs to the user and return
        if self.__standalone:
            Logger.print_ok("The following MCUs were found:", prefix=False)
            for i, mcu in enumerate(self.flash_options.mcu_list):
                print(f"   ● MCU #{i}: {Color.CYAN}{mcu}{Color.RST}")
            time.sleep(3)
            return

        self.goto_next_menu()

    def goto_next_menu(self, **kwargs):
        KlipperSelectMcuIdMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectMcuIdMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "!!! ATTENTION !!!"
        self.title_style = MenuTitleStyle.PLAIN
        self.title_color = Color.RED
        self.flash_options = FlashOptions()
        self.mcu_list = self.flash_options.mcu_list
        self.input_label_txt = "Select MCU to flash"
        self.footer_type = FooterType.BACK

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = (
            previous_menu
            if previous_menu is not None
            else KlipperSelectMcuConnectionMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{i}": Option(self.flash_mcu, f"{i}") for i in range(len(self.mcu_list))
        }

    def print_menu(self) -> None:
        header2 = f"[{Color.apply('List of detected MCUs', Color.CYAN)}]"
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Make sure, to select the correct MCU!                 ║
            ║ ONLY flash a firmware created for the respective MCU! ║
            ║                                                       ║
            ╟{header2:─^64}╢
            ║                                                       ║
            """
        )[1:]

        for i, mcu in enumerate(self.mcu_list):
            mcu = mcu.split("/")[-1]
            menu += f"║ {i}) {Color.apply(f'{mcu:<51}', Color.CYAN)}║\n"

        menu += textwrap.dedent(
            """
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def flash_mcu(self, **kwargs):
        try:
            index: int | None = kwargs.get("opt_index", None)
            if index is None:
                raise Exception("opt_index is None")

            index = int(index)
            selected_mcu = self.mcu_list[index]
            self.flash_options.selected_mcu = selected_mcu

            if self.flash_options.flash_method == FlashMethod.SD_CARD:
                KlipperSelectSDFlashBoardMenu(previous_menu=self.__class__).run()
            elif self.flash_options.flash_method == FlashMethod.REGULAR:
                KlipperFlashOverviewMenu(previous_menu=self.__class__).run()
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Flashing failed!")


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectSDFlashBoardMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.flash_options = FlashOptions()
        self.available_boards = get_sd_flash_board_list()
        self.input_label_txt = "Select board type"

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = (
            previous_menu if previous_menu is not None else KlipperSelectMcuIdMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{i}": Option(self.board_select, f"{i}")
            for i in range(len(self.available_boards))
        }

    def print_menu(self) -> None:
        if len(self.available_boards) < 1:
            KlipperNoBoardTypesErrorMenu().run()
        else:
            menu = textwrap.dedent(
                """
                ║ Please select the type of board that corresponds to   ║
                ║ the currently selected MCU ID you chose before.       ║
                ║                                                       ║
                ║ The following boards are currently supported:         ║
                ╟───────────────────────────────────────────────────────╢
                """
            )[1:]

            for i, board in enumerate(self.available_boards):
                line = f" {i}) {board}"
                menu += f"║{line:<55}║\n"
            menu += "╟───────────────────────────────────────────────────────╢"
            print(menu, end="")

    def board_select(self, **kwargs):
        try:
            index: int | None = kwargs.get("opt_index", None)
            if index is None:
                raise Exception("opt_index is None")

            index = int(index)
            self.flash_options.selected_board = self.available_boards[index]
            self.baudrate_select()
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Board selection failed!")

    def baudrate_select(self, **kwargs):
        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                "If your board is flashed with firmware that connects "
                "at a custom baud rate, please change it now.",
                "\n\n",
                "If you are unsure, stick to the default 250000!",
            ],
        )
        self.flash_options.selected_baudrate = get_number_input(
            question="Please set the baud rate",
            default=250000,
            min_value=0,
            allow_go_back=True,
        )
        KlipperFlashOverviewMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashOverviewMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "!!! ATTENTION !!!"
        self.title_style = MenuTitleStyle.PLAIN
        self.title_color = Color.RED
        self.flash_options = FlashOptions()
        self.input_label_txt = "Perform action (default=Y)"

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_options(self) -> None:
        self.options = {
            "y": Option(self.execute_flash),
            "n": Option(self.abort_process),
        }

        self.default_option = Option(self.execute_flash)

    def print_menu(self) -> None:
        method = self.flash_options.flash_method.value
        command = self.flash_options.flash_command.value
        conn_type = self.flash_options.connection_type.value
        mcu = self.flash_options.selected_mcu.split("/")[-1]
        board = self.flash_options.selected_board
        baudrate = self.flash_options.selected_baudrate
        kconfig = Path(self.flash_options.selected_kconfig).name
        color = Color.CYAN
        subheader = f"[{Color.apply('Overview', color)}]"
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Before contuining the flashing process, please check  ║
            ║ if all parameters were set correctly! Once you made   ║
            ║ sure everything is correct, start the process. If any ║
            ║ parameter needs to be changed, you can go back (B)    ║
            ║ step by step or abort and start from the beginning.   ║
            ║{subheader:─^64}║
            ║                                                       ║
            """
        )[1:]

        menu += textwrap.dedent(
            f"""
            ║ MCU: {Color.apply(f"{mcu:<48}", color)} ║
            ║ Connection: {Color.apply(f"{conn_type:<41}", color)} ║
            ║ Flash method: {Color.apply(f"{method:<39}", color)} ║
            ║ Flash command: {Color.apply(f"{command:<38}", color)} ║
            """
        )[1:]

        if self.flash_options.flash_method is FlashMethod.SD_CARD:
            menu += textwrap.dedent(
                f"""
                ║ Board type: {Color.apply(f"{board:<41}", color)} ║
                ║ Baudrate: {Color.apply(f"{baudrate:<43}", color)} ║
                """
            )[1:]

        if self.flash_options.flash_method is FlashMethod.REGULAR:
            menu += textwrap.dedent(
                f"""
                ║ Firmware config: {Color.apply(f"{kconfig:<36}", color)} ║
                """
            )[1:]

        menu += textwrap.dedent(
            """
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            ║  Y) Start flash process                               ║
            ║  N) Abort - Return to Advanced Menu                   ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def execute_flash(self, **kwargs):
        start_flash_process(self.flash_options)
        Logger.print_info("Returning to MCU Flash Menu in 5 seconds ...")
        time.sleep(5)
        KlipperFlashMethodMenu().run()

    def abort_process(self, **kwargs):
        from core.menus.advanced_menu import AdvancedMenu

        AdvancedMenu().run()
