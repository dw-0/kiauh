# Installing KIAUH

In the following sections, you will be guided through the installation
process step-by-step.

To use KIAUH, it is enough to download the script and run it on your
Raspberry Pi or other compatible device. If you need to know how to
set up a Raspberry Pi or if you are unsure whether your current setup
is sufficient, please refer to the [Raspberry Pi Installation Guide](raspberry-pi-setup.md)
and follow the steps therein. Afterwards, you can return to this guide to install KIAUH.

### Prerequisites
Before you can download and run KIAUH, you need to ensure that ``git`` is
installed on your system. Open a terminal and run the following command:

```bash
sudo apt-get update && sudo apt-get install git -y
```

### Downloading KIAUH
After `git` was successfully installed, you can download KIAUH by
cloning the repository from GitHub. It is recommended to clone it into
your home directory. Run the following command in your terminal:
```bash
cd ~ && git clone https://github.com/dw-0/kiauh.git
```

### Running KIAUH
Once the repository is cloned, you can start KIAUH. Make sure you are in
your home directory and execute the script by running the following
command:
```bash
./kiauh/kiauh.sh
```

After executing the command, you will be presented with the KIAUH menu,
which allows you to install and manage various 3D printing software.
For more information on how to use KIAUH, please refer to the
[Usage Guide](usage.md).
