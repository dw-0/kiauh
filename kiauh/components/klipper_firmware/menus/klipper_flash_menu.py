# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper_firmware.flash_options import (
    FlashOptions,
    FlashMethod,
    FlashCommand,
    ConnectionType,
)
from components.klipper_firmware.flash_utils import (
    find_usb_device_by_id,
    find_uart_device,
    find_usb_dfu_device,
    flash_device,
)
from core.menus import FooterType

from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_CYAN, RESET_FORMAT, COLOR_YELLOW, COLOR_RED
from utils.input_utils import get_confirm
from utils.logger import Logger


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashMethodMenu(BaseMenu):
    def __init__(self):
        super().__init__()
        self.header = False
        self.options = {
            "1": self.select_regular,
            "2": self.select_sdcard,
            "h": KlipperFlashMethodHelpMenu,
        }
        self.input_label_txt = "Select flash method"
        self.footer_type = FooterType.BACK_HELP

        self.flash_options = FlashOptions()

    def print_menu(self) -> None:
        header = " [ Flash MCU ] "
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Please select the flashing method to flash your MCU.  |
            | Make sure to only select a method your MCU supports.  |
            | Not all MCUs support both methods!                    |
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
        next_menu = KlipperFlashCommandMenu(previous_menu=self)
        next_menu.run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperFlashCommandMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()
        self.header = False
        self.options = {
            "1": self.select_flash,
            "2": self.select_serialflash,
            "h": KlipperFlashCommandHelpMenu,
        }
        self.default_option = self.select_flash
        self.input_label_txt = "Select flash command"
        self.previous_menu = previous_menu
        self.footer_type = FooterType.BACK_HELP

        self.flash_options = FlashOptions()

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
        next_menu = KlipperSelectMcuConnectionMenu(previous_menu=self)
        next_menu.run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectMcuConnectionMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()
        self.header = False
        self.options = {
            "1": self.select_usb,
            "2": self.select_dfu,
            "3": self.select_usb_dfu,
            "h": KlipperMcuConnectionHelpMenu,
        }
        self.input_label_txt = "Select connection type"
        self.previous_menu = previous_menu
        self.footer_type = FooterType.BACK_HELP

        self.flash_options = FlashOptions()

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
        else:
            self.goto_next_menu()

    def goto_next_menu(self, **kwargs):
        next_menu = KlipperSelectMcuIdMenu(previous_menu=self)
        next_menu.run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperSelectMcuIdMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()
        self.header = False
        self.flash_options = FlashOptions()
        self.mcu_list = self.flash_options.mcu_list
        options = {f"{index}": self.flash_mcu for index in range(len(self.mcu_list))}
        self.options = options
        self.input_label_txt = "Select MCU to flash"
        self.previous_menu = previous_menu
        self.footer_type = FooterType.BACK_HELP

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

        print(f"{COLOR_CYAN}###### You selected:{RESET_FORMAT}")
        print(f"● MCU #{index}: {selected_mcu}\n")

        if get_confirm("Continue", allow_go_back=True):
            Logger.print_status(f"Flashing '{selected_mcu}' ...")
            flash_device(self.flash_options)

        self.goto_next_menu()

    def goto_next_menu(self, **kwargs):
        pass
        # TODO: navigate back to advanced menu after flashing

        # from core.menus.main_menu import MainMenu
        # from core.menus.advanced_menu import AdvancedMenu
        #
        # next_menu = AdvancedMenu()
        # next_menu.start()


class KlipperFlashMethodHelpMenu(BaseMenu):
    def __init__(self):
        super().__init__()
        self.header = False

    def print_menu(self) -> None:
        header = " < ? > Help: Flash MCU < ? > "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        subheader1 = f"{COLOR_CYAN}Regular flashing method:{RESET_FORMAT}"
        subheader2 = f"{COLOR_CYAN}Updating via SD-Card Update:{RESET_FORMAT}"
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {subheader1:<62} |
            | The default method to flash controller boards which   |
            | are connected and updated over USB and not by placing |
            | a compiled firmware file onto an internal SD-Card.    |
            |                                                       |
            | Common controllers that get flashed that way are:     |
            | - Arduino Mega 2560                                   |
            | - Fysetc F6 / S6 (used without a Display + SD-Slot)   |
            |                                                       |
            | {subheader2:<62} |
            | Many popular controller boards ship with a bootloader |
            | capable of updating the firmware via SD-Card.         |
            | Choose this method if your controller board supports  |
            | this way of updating. This method ONLY works for up-  |
            | grading firmware. The initial flashing procedure must |
            | be done manually per the instructions that apply to   |
            | your controller board.                                |
            |                                                       |
            | Common controllers that can be flashed that way are:  |
            | - BigTreeTech SKR 1.3 / 1.4 (Turbo) / E3 / Mini E3    |
            | - Fysetc F6 / S6 (used with a Display + SD-Slot)      |
            | - Fysetc Spider                                       |
            |                                                       |
            """
        )[1:]
        print(menu, end="")


class KlipperFlashCommandHelpMenu(BaseMenu):
    def __init__(self):
        super().__init__()
        self.header = False

    def print_menu(self) -> None:
        header = " < ? > Help: Flash MCU < ? > "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        subheader1 = f"{COLOR_CYAN}make flash:{RESET_FORMAT}"
        subheader2 = f"{COLOR_CYAN}make serialflash:{RESET_FORMAT}"
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {subheader1:<62} |
            | The default command to flash controller board, it     |
            | will detect selected microcontroller and use suitable |
            | tool for flashing it.                                 |
            |                                                       |
            | {subheader2:<62} |
            | Special command to flash STM32 microcontrollers in    |
            | DFU mode but connected via serial. stm32flash command |
            | will be used internally.                              |
            |                                                       |
            """
        )[1:]
        print(menu, end="")


class KlipperMcuConnectionHelpMenu(BaseMenu):
    def __init__(self):
        super().__init__()
        self.header = False

    def print_menu(self) -> None:
        header = " < ? > Help: Flash MCU < ? > "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        subheader1 = f"{COLOR_CYAN}USB:{RESET_FORMAT}"
        subheader2 = f"{COLOR_CYAN}UART:{RESET_FORMAT}"
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {subheader1:<62} |
            | Selecting USB as the connection method will scan the  |
            | USB ports for connected controller boards. This will  |
            | be similar to the 'ls /dev/serial/by-id/*' command    |
            | suggested by the official Klipper documentation for   |
            | determining successfull USB connections!              |
            |                                                       |
            | {subheader2:<62} |
            | Selecting UART as the connection method will list all |
            | possible UART serial ports. Note: This method ALWAYS  |
            | returns something as it seems impossible to determine |
            | if a valid Klipper controller board is connected or   |
            | not. Because of that, you MUST know which UART serial |
            | port your controller board is connected to when using |
            | this connection method.                               |
            |                                                       |
            """
        )[1:]
        print(menu, end="")
