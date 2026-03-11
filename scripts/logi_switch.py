#!/usr/bin/env python3
"""Switch Logitech devices between computers with hidapitester."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "local.json"
DEFAULT_HIDAPITESTER = {
    "Windows": REPO_ROOT / "vendor" / "input-switcher" / "windows" / "hidapitester.exe",
    "Darwin": REPO_ROOT / "vendor" / "input-switcher" / "mac" / "hidapitester",
    "Linux": REPO_ROOT / "vendor" / "input-switcher" / "linux" / "hidapitester",
}


class ConfigError(RuntimeError):
    pass


def load_config(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(
            f"Missing config file: {path}\n"
            "Copy config/local.example.json to config/local.json and edit it first."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc


def current_os_name() -> str:
    name = platform.system()
    if name not in DEFAULT_HIDAPITESTER:
        raise ConfigError(f"Unsupported platform: {name}")
    return name


def resolve_target_name(config: dict, requested_target: str | None) -> str:
    aliases = config.get("aliases", {})
    target_name = requested_target
    if target_name is None:
        os_name = current_os_name()
        default_targets = config.get("default_targets", {})
        target_name = default_targets.get(os_name)
        if not target_name:
            raise ConfigError(f"No default target configured for {os_name}")
    return aliases.get(target_name, target_name)


def resolve_hidapitester(config: dict) -> Path:
    os_name = current_os_name()
    configured = config.get("hidapitester_path", {}).get(os_name)
    path = Path(configured) if configured else DEFAULT_HIDAPITESTER[os_name]
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.exists():
        raise ConfigError(f"hidapitester binary not found: {path}")
    return path


def validate_command(command: dict, target_name: str) -> None:
    if "selector" not in command or not isinstance(command["selector"], list):
        raise ConfigError(f"Target '{target_name}' has a command without a selector list")
    if "length" not in command:
        raise ConfigError(f"Target '{target_name}' has a command without a length")
    if "report" not in command:
        raise ConfigError(f"Target '{target_name}' has a command without a report")


def command_args(binary: Path, command: dict) -> list[str]:
    args = [str(binary)]
    args.extend(str(part) for part in command["selector"])
    args.extend(["--open", "--length", str(command["length"]), "--send-output", str(command["report"])])
    return args


def run_target(config: dict, target_name: str | None, dry_run: bool) -> int:
    targets = config.get("targets", {})
    resolved_target = resolve_target_name(config, target_name)
    if resolved_target not in targets:
        available_names = sorted({*targets.keys(), *config.get("aliases", {}).keys()})
        available = ", ".join(available_names) or "<none>"
        raise ConfigError(f"Unknown target '{target_name or '<default>'}'. Available targets: {available}")

    binary = resolve_hidapitester(config)
    target = targets[resolved_target]
    commands = target.get("commands", [])
    if not commands:
        raise ConfigError(f"Target '{resolved_target}' has no commands")

    for command in commands:
        validate_command(command, resolved_target)
        args = command_args(binary, command)
        name = command.get("name", "device")
        label = resolved_target if target_name is None or target_name == resolved_target else f"{target_name} -> {resolved_target}"
        print(f"[logi-switch] {label}: {name}")
        print(" ", " ".join(args))
        if dry_run:
            continue
        completed = subprocess.run(args, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def list_devices(config: dict) -> int:
    binary = resolve_hidapitester(config)
    args = [str(binary), "--list-detail"]
    print(" ", " ".join(args))
    completed = subprocess.run(args, check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Config path (default: {DEFAULT_CONFIG})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    switch_parser = subparsers.add_parser("switch", help="Run all commands for a target")
    switch_parser.add_argument("target", help="Target name from config, for example 'windows' or 'mac'")
    switch_parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")

    default_switch_parser = subparsers.add_parser(
        "switch-default",
        help="Run all commands for the current platform's configured default target",
    )
    default_switch_parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")

    subparsers.add_parser("list-devices", help="Run hidapitester --list-detail on this machine")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(Path(args.config).resolve())
    if args.command == "switch":
        return run_target(config, args.target, args.dry_run)
    if args.command == "switch-default":
        return run_target(config, None, args.dry_run)
    if args.command == "list-devices":
        return list_devices(config)
    raise ConfigError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ConfigError as exc:
        print(f"[logi-switch] {exc}", file=sys.stderr)
        raise SystemExit(2)
