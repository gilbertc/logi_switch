# logi_switch

Repo-local wrappers around [`marcelhoffs/input-switcher`](https://github.com/marcelhoffs/input-switcher) and [`todbot/hidapitester`](https://github.com/todbot/hidapitester) so you can bind one shortcut per machine:

- On Windows: `Ctrl+F1` can invoke the Windows-default wrapper, which targets channel 3 in the example config.
- On macOS: `Ctrl+F1` can invoke the macOS-default wrapper, which targets channel 1 in the example config.
- On Linux: use the Linux-default wrapper, which also targets channel 1 in the example config.

The upstream repos are included as submodules under `vendor/` so both machines can clone the same repo and run the same wrappers.

## What is in this repo

- `vendor/input-switcher`
- `vendor/hidapitester`
- `scripts/logi_switch.py`: reads local config and runs the right `hidapitester` commands
- `scripts/windows/`: Windows `.cmd` launchers
- `scripts/macos/`: macOS `.sh` launchers
- `scripts/linux/`: Linux `.sh` launchers
- `scripts/switch-to-mac.*`
- `scripts/switch-to-windows.*`
- `scripts/list-devices.*`
- `hotkeys/windows/LogiSwitch.ahk`: AutoHotkey example
- `hotkeys/macos/logi-switch.lua`: Hammerspoon example

## Upstream review

`input-switcher` is useful, but it is sample code, not a finished cross-platform tool:

- It hard-codes one-way commands for a specific device set.
- The Windows/Linux scripts assume fixed receiver and device IDs.
- The macOS README still talks about an `osx` folder even though the repo now uses `mac/`.
- It mixes setup guidance with reverse-engineering notes, so the important parts are easy to miss.

`hidapitester` is the stronger dependency:

- It is small and well-scoped.
- Its CLI is stable enough for wrappers like this.
- The vendored binaries inside `vendor/input-switcher` are already enough for Windows, macOS, and Linux, so you do not need a separate install just to test switching.

What you may still need per OS:

- Windows: nothing extra beyond Python 3 for the wrapper and AutoHotkey if you want the sample hotkey.
- macOS: no extra `hidapitester` install, but Gatekeeper may ask you to allow the bundled binary the first time you run it.
- Linux: no extra `hidapitester` install, but you may need the supplied udev rule or root privileges to access the receiver.

## Verified findings

These findings were verified on your Windows machine with a Logi Bolt receiver (`046D:C548`) and an MX Mechanical Mini + MX Master 4:

- Keyboard switching on Bolt is a single 7-byte report.
- Mouse switching on Bolt for the MX Master 4 is also a 7-byte report, but it is not the same payload used by older MX Master 3S examples.
- A mixed keyboard+mouse capture was noisy enough to be misleading.
- A mouse-only Wireshark capture showed the actual minimal mouse switch command.

Verified Windows -> Mac / channel 2 commands:

```text
Keyboard: 0x10,0x01,0x09,0x1e,0x01,0x00,0x00
Mouse:    0x10,0x02,0x0e,0x18,0x01,0x00,0x00
```

The mouse discovery matters because earlier guesses based on MX Master 3S-style payloads did not work:

```text
0x10,0x02,0x0a,0x1b,0x01,0x00,0x00
0x10,0x02,0x0a,0x1e,0x01,0x00,0x00
```

Those older examples are still useful as reverse-engineering hints, but they are not portable across mouse models.

## Setup

### 1. Clone with submodules

```bash
git clone --recurse-submodules <your-repo-url>
```

If you already cloned the repo:

```bash
git submodule update --init --recursive
```

### 2. Create your local config on each machine

Copy [config/local.example.json](/home/gcheung/repo/logi_switch/config/local.example.json) to `config/local.json` and edit it.

Each machine keeps its own `config/local.json`. That matters because receiver IDs and device numbering can differ between the Windows-side receiver and the Mac-side receiver.

The config is channel-based, with optional aliases:

- `targets.channel-1`, `targets.channel-2`, `targets.channel-3`: the exact reports for those Easy-Switch channels on this clone
- `default_targets`: which channel each OS-specific `switch-default` launcher should run
- `aliases`: optional semantic names, so legacy wrappers such as `switch-to-windows.*` can still resolve to a channel target

The example config currently defaults to:

- Windows -> `channel-3`
- macOS -> `channel-1`
- Linux -> `channel-1`

For your current verified Windows-side Bolt setup, `channel-2` in the example config is already populated with directly verified values for:

- MX Mechanical Mini -> channel 2
- MX Master 4 -> channel 2

The channel 1 and channel 3 values in the example follow the same pattern by changing only the channel byte. Verify them on your hardware.

Each command contains:

- `selector`: the `hidapitester` device selector for the device or receiver that is currently connected to this machine
- `length`: report length, usually `7` for receiver/Bolt switching and `20` for Bluetooth switching
- `report`: the exact output report to send

### 3. Discover the current machine's HID targets

On Windows:

```powershell
scripts\windows\list-devices.cmd
```

On macOS or Linux:

```bash
./scripts/macos/list-devices.sh
./scripts/linux/list-devices.sh
```

This runs `hidapitester --list-detail`.

For Bolt/receiver-based switching, look for the Logitech receiver, for example `046D:C548`.

For Bluetooth switching, the keyboard and mouse usually show up as separate devices and you will need their own `--vidpid`, `--usage`, and `--usagePage` values.

### 4. Fill in your reports

In the report payload, the channel byte works like this:

- channel 1 -> `0x00`
- channel 2 -> `0x01`
- channel 3 -> `0x02`

The video description you pasted gave a correct MX Mechanical Mini sample for Bolt, and the later Windows capture confirmed the same keyboard payload:

```text
Channel 1: 0x10,0x01,0x09,0x1e,0x00,0x00,0x00
Channel 2: 0x10,0x01,0x09,0x1e,0x01,0x00,0x00
Channel 3: 0x10,0x01,0x09,0x1e,0x02,0x00,0x00
```

For the MX Master 4 on Bolt, the working channel 2 payload is:

```text
Channel 2: 0x10,0x02,0x0e,0x18,0x01,0x00,0x00
```

That value came from a mouse-only USB capture of Logi Options+ and was then replayed successfully with `hidapitester`.

The likely channel 1 form is:

```text
Channel 1: 0x10,0x02,0x0e,0x18,0x00,0x00,0x00
```

The likely channel 3 form is:

```text
Channel 3: 0x10,0x02,0x0e,0x18,0x02,0x00,0x00
```

If one side uses Bluetooth instead of Bolt/receiver, use a `length` of `20` and keep device-specific selectors per command. The video description you pasted matches that pattern already.

### 5. Test before binding keys

On Windows:

```powershell
scripts\windows\switch-default.cmd --dry-run
scripts\windows\switch-default.cmd
```

On macOS:

```bash
./scripts/macos/switch-default.sh --dry-run
./scripts/macos/switch-default.sh
```

On Linux:

```bash
./scripts/linux/switch-default.sh --dry-run
./scripts/linux/switch-default.sh
```

If the dry run looks right but the switch fails, the usual causes are:

- wrong receiver/device ID in `selector`
- wrong device number inside the report
- wrong report bytes for the mouse
- different connection type on this machine than you assumed

## Hotkeys

### Windows

Use [hotkeys/windows/LogiSwitch.ahk](/home/gcheung/repo/logi_switch/hotkeys/windows/LogiSwitch.ahk) with AutoHotkey v2.

That file binds `Ctrl+F1` to `scripts/windows/switch-default.cmd`.

With the example config, that means Windows defaults to channel 3. If you want a different Windows default, change `default_targets.Windows` in your local config.

### macOS

Use [hotkeys/macos/logi-switch.lua](/home/gcheung/repo/logi_switch/hotkeys/macos/logi-switch.lua) with Hammerspoon.

Edit the `repo` variable to your absolute clone path, then load it from your `~/.hammerspoon/init.lua`:

```lua
dofile("/absolute/path/to/logi_switch/hotkeys/macos/logi-switch.lua")
```

That file binds `Ctrl+F1` to `scripts/macos/switch-default.sh`.

Hammerspoon is the cleanest macOS hotkey option for this repo because it can launch your local shell wrapper directly and stay version-controlled with the rest of the setup. If you do not want Hammerspoon, the next-best options are Keyboard Maestro or Karabiner-Elements plus a shell command.

With the example config, macOS defaults to channel 1. If you want a different macOS default, change `default_targets.Darwin` in your local config.

If macOS is treating `F1` as brightness instead of a standard function key, you may need to use `fn+ctrl+F1` or enable standard function key behavior in macOS settings.

### Linux

Linux does not need a repo-specific hotkey helper file. Use your desktop environment's normal custom shortcut mechanism and point it at `scripts/linux/switch-default.sh`.

## Current state

What is complete:

- Windows-side Bolt receiver detection
- Windows-side keyboard -> Mac command
- Windows-side mouse -> Mac command
- platform-packaged wrappers under `scripts/windows`, `scripts/macos`, and `scripts/linux`
- configurable per-OS default targets
- repo-local wrapper scripts
- AutoHotkey example for `Ctrl+F1`
- Hammerspoon example for `Ctrl+F1`

What remains:

- capture and verify the actual channel 1 mouse report if the inferred/default values do not work on every machine
- verify the inferred channel 3 mouse report on your hardware
