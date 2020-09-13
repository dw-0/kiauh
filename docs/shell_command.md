# Shell Command Extension

### Creator of this extension is [Arksine](https://github.com/Arksine).

This is a brief explanation of how to use the shell command extension for Klipper, which you can install with KIAUH.

After installing the extension you can execute linux commands or even scripts from within Klipper with custom commands defined in your printer.cfg.

#### How to configure a shell command:

```shell
# Runs a linux command or script from within klipper.  Note that sudo commands
# that require password authentication are disallowed. All executable scripts
# should include a shebang.
# [shell_command my_shell_cmd]
#command:
#  The linux shell command/script to be executed.  This parameter must be
#  provided
#timeout: 2.
#  The timeout in seconds until the command is forcably terminated.  Default
#  is 2 seconds.
#verbose: True
#  If enabled, the command's output will be forwarded to the terminal.  Its
#  recommended to set this to false for commands that my run in quick
#  succession.  Default is True.
```

Once you have set up a shell command with the given parameters from above in your printer.cfg you can run the command as follows:
`RUN_SHELL_COMMAND CMD=name`

Example:

```
[shell_command hello_world]
command: echo hello world
timeout: 2.
verbose: True
```

Execute with:
`RUN_SHELL_COMMAND CMD=hello_world`

## Warning

This extension may have a high potential for abuse if not used carefully! Also, depending on the command you execute, high system loads may occur and can cause system instabilities.
Use this extension at your own risk and only if you know what you are doing!
