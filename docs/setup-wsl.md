# R1 ROS in Windows
This uses WSL and Visual Studio Code.

## Setting up WSL2 ##
- Install WSL2 (Default) using a Command Prompt (Run as administrator) with `wsl --install`
- After that, install Ubuntu 24.04 from the Microsoft Store (required for ROS 2 Jazzy).
With `wsl --list --verbose`, you should see this:
```
  NAME             STATE       VERSION
* Ubuntu-24.04    Running         2
```

## Sharing USB devices from Windows to WSL2 ##

- Requirement: [usbipd](https://github.com/dorssel/usbipd-win)
- Install usbipd using an elevated Command Prompt (Run as administrator):
```
winget install usbipd
```

- By default devices are not shared with USBIP clients. To lookup and share devices, run:
```
usbipd list
usbipd bind --busid=<BUSID>
```
- Replace `<BUSID>` with the ID, example: `1-2`. This will share the device.
- Attach the device to WSL2 from within Windows:
```
usbipd attach --wsl --busid=<BUSID>
```

## Open WSL in Visual Studio Code in Ubuntu ##
Install the `WSL extension` on your host VS-Code. This allows you to open a folder in WSL. Install other necessary extensions as well. Navigate to the home directory, open a VS-Code terminal and follow the [readme](README.md).