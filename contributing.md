# Contributing

## API
The kiauh Python module includes facilities to start, monitor, and sometimes even supersede the install and uninstall scripts of programs in the Kiauh menu (kiauh.sh). This sometimes includes the utilization of dependency metadata files, or even reading dependencies from bash script variables. A December 2025 branch (crossplatform) adds features to translate all apt (or apt-get) commands in a script, and translate package names there or elsewhere to package names from other distros. This is possible using the branch's package name conversion table in distros.json. Even if the packages are not converted,

### API Development
Before Dec 2025 the original kiauh.sh was gradually becoming a program to install anything, even having a partial bash interpreter. However, kiauh.sh and indeed many of the 3D printer server backend features for Klipper have scripts that assume a debian-based distro, with an emphasis on Raspberry Pi OS (formerly Raspbian). That is understandable since various Raspberry Pi models commonly run that OS and commonly run 3D printers. However, special kernel adjustments are necessary for repurposed (rooted UEFI) tablets which would otherwise be useless (due to being stuck on Windows 8 or so, and slow for that purpose), such as the Surface RT which has the NVIDIA Tegra 3 chipset. KlipperRT made advances in the area but it is a binary ISO blob that isn't reproducible and on which the kernel would be difficult to upgrade. The customized kernel is hard-coded to completely block contiguous memory above a certain amount, so there is no known (or at least commonly used) webcam library which will work on it (unless perhaps you use a 320x240 camera with hardware-based mjpeg, but this is untested). On the other hand, postmarketOS (based on Alpine Linux) and arch have workarounds for the contiguous memory limitation. The addition of cross-distro features (which could potentially be adapted slightly for cross-platform use) to the kiauh Python module allows apt script lines to be translated to postmarketOS (and likely Alpine Linux and any distro based on it). Fedora (and fedora-based distros) and Arch (and arch-based distros) are implemented (in the form of translated package commands, and package names in distros.json) but more testing is required for those distros. Other distros are a work in progress (some caveats are implemented in Python, but package names are missing or incomplete from distros.json).

### API Usage
You can create additional menu items in Kiauh.sh, but it is likely you will need to add more features to the kiauh Python module or more package names to distros.json. However, if you read the "API Development" section above you will understand how to use and improve existing features so that the code can become stable and adaptable rather than redundant (Warning: "AI" [LLM] sites/programs are notorious at creating redundant code and hallucinating package names, API function names, config variable names, etc). You can use the framework for uses not specific to 3D printers, with the caveat that if there are packages that are not used by kiauh.sh (packages that aren't dependencies of Klipper, Moonraker, Fluidd, etc.) and the package name differs (and can't be computed by `translate_deb_package_name`), the apt install command will be translated to use your distro's package manager if it is in the PATH, but the install command will fail due to an incorrect package, usually halting the install (Normally in this case kiauh.sh will correctly mark the program as "Incomplete" if it is one of the programs on the menu). For a full application that uses all features, see kiauh.sh. To use the aspects of it apart from 3D printers, use the translate_* functions (translate_script_file, translate_script, translate_script_line, translate_deb_package_names, translate_deb_package_name in order from high-level to low-level) and all the complicated magic happens automatically--For example, on Fedora, translate_script_file would both use of translate_deb_package_name and change apt commands to dnf or yum, in that order of precedence, including the relevant arguments.

- If creating a new installer, you can simply use the functions
  in the sys_utils module if no custom behavior is necessary:
```Python
from kiauh.utils import sys_utils
# ^ importing the whole sys_utils module is helpful such as
#   if you have code completion in your code editor.
# sys_utils.save_distros_meta()
from kiauh.utils.common import check_install_dependencies
deps = ["libusb-1.0"]
check_install_dependencies(deps)
# ^ For help using the sys_utils module, read the code of the
#   check_install_dependencies function and look the docstring
#   of each function called there.
# ^ If the "apt" or "apt-get"
#   command is not detected in the PATH, but the "dnf" or "yum"
#   command is, then the following will run (including
#   package name translation, which is automatic):
#   sudo dnf -y install libusb-1  # or yum if present and dnf is not.
```

For status on feature completion (initially in the crossplatform branch of https://github.com/Hierosoft/kiauh.git), see:
<https://github.com/dw-0/kiauh/issues/749>

## Known issues
- [ ] CentOS and variants where package names may differ (would require a separate branch of package names, or a hierarchy feature utilizing a smaller dictionary as a partial overlay for addition/replacement)
