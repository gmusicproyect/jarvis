"""Autostart — LaunchAgent / Startup / systemd."""

from __future__ import annotations

from pathlib import Path

from jarvis.config.loader import project_root
from jarvis.platform import PlatformName, detect_platform
from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.autostart")


def launchagent_plist(
    *,
    label: str = "com.jarvis.assistant",
    minimized: bool = True,
) -> str:
    root = project_root()
    start = root / "scripts" / "start_jarvis.sh"
    program = f"{start} gui" if minimized else f"{start}"
    # Use poetry run via script
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>cd "{root}" && ./scripts/start_jarvis.sh gui</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>{root}/data/logs/launchagent.out.log</string>
  <key>StandardErrorPath</key>
  <string>{root}/data/logs/launchagent.err.log</string>
</dict>
</plist>
"""


def systemd_user_unit() -> str:
    root = project_root()
    return f"""[Unit]
Description=Jarvis Personal Assistant
After=default.target

[Service]
Type=simple
WorkingDirectory={root}
ExecStart=/bin/bash -lc 'cd "{root}" && ./scripts/start_jarvis.sh gui'
Restart=on-failure

[Install]
WantedBy=default.target
"""


def windows_startup_cmd() -> str:
    root = project_root()
    return f'@echo off\r\ncd /d "{root}"\r\npoetry run jarvis gui\r\n'


def install_autostart(*, minimized: bool = True) -> Path:
    platform = detect_platform()
    if platform == PlatformName.MACOS:
        dest = Path.home() / "Library" / "LaunchAgents" / "com.jarvis.assistant.plist"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(launchagent_plist(minimized=minimized), encoding="utf-8")
        _LOG.info("autostart_installed", path=str(dest), platform="macos")
        return dest
    if platform == PlatformName.LINUX:
        dest = Path.home() / ".config" / "systemd" / "user" / "jarvis.service"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(systemd_user_unit(), encoding="utf-8")
        _LOG.info("autostart_installed", path=str(dest), platform="linux")
        return dest
    if platform == PlatformName.WINDOWS:
        dest = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
            / "jarvis.cmd"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(windows_startup_cmd(), encoding="utf-8")
        _LOG.info("autostart_installed", path=str(dest), platform="windows")
        return dest
    raise NotImplementedError(f"Autostart no soportado en {platform}")


def uninstall_autostart() -> None:
    platform = detect_platform()
    paths = []
    if platform == PlatformName.MACOS:
        paths.append(Path.home() / "Library" / "LaunchAgents" / "com.jarvis.assistant.plist")
    elif platform == PlatformName.LINUX:
        paths.append(Path.home() / ".config" / "systemd" / "user" / "jarvis.service")
    elif platform == PlatformName.WINDOWS:
        paths.append(
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
            / "jarvis.cmd"
        )
    for p in paths:
        if p.exists():
            p.unlink()
            _LOG.info("autostart_removed", path=str(p))
