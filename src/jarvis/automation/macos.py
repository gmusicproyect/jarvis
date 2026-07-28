"""Controladores macOS nativos (open, osascript, pbcopy, screencapture)."""

from __future__ import annotations

import shutil
import shlex
import subprocess
from pathlib import Path

from jarvis.utils.logging import get_logger

_LOG = get_logger("jarvis.automation.macos")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
    )


def _osascript(script: str) -> str:
    result = _run(["osascript", "-e", script])
    return (result.stdout or "").strip()


class MacApplicationController:
    name = "macos_app"

    def open_app(self, app_name: str) -> None:
        _run(["open", "-a", app_name])

    def close_app(self, app_name: str) -> None:
        _osascript(f'tell application "{app_name}" to quit')

    def is_running(self, app_name: str) -> bool:
        out = _osascript(
            f'tell application "System Events" to '
            f'(name of processes) contains "{app_name}"'
        )
        return out.lower() == "true"


class MacFileController:
    name = "macos_file"

    def open_path(self, path: Path) -> None:
        _run(["open", str(path.expanduser())])

    def open_folder(self, path: Path) -> None:
        p = path.expanduser()
        if p.is_file():
            p = p.parent
        _run(["open", str(p)])

    def find(self, name: str, root: Path | None = None) -> list[Path]:
        root = (root or Path.home()).expanduser()
        matches: list[Path] = []
        # mdfind es rápido en macOS; fallback a rglob limitado
        try:
            query = f'kMDItemFSName == "{name}"c'
            result = _run(
                ["mdfind", "-onlyin", str(root), query],
                check=False,
            )
            for line in (result.stdout or "").splitlines():
                p = Path(line.strip())
                if p.exists():
                    matches.append(p)
                if len(matches) >= 20:
                    break
        except Exception:  # noqa: BLE001
            pass
        if matches:
            return matches
        for p in root.rglob(name):
            matches.append(p)
            if len(matches) >= 20:
                break
        return matches

    def move(self, src: Path, dest: Path) -> Path:
        src, dest = src.expanduser(), dest.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        return dest

    def copy(self, src: Path, dest: Path) -> Path:
        src, dest = src.expanduser(), dest.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            return Path(shutil.copytree(str(src), str(dest)))
        return Path(shutil.copy2(str(src), str(dest)))

    def rename(self, src: Path, new_name: str) -> Path:
        src = src.expanduser()
        dest = src.with_name(new_name)
        src.rename(dest)
        return dest

    def trash(self, path: Path) -> None:
        path = path.expanduser()
        # Finder trash (recuperable)
        _osascript(
            f'tell application "Finder" to delete '
            f'(POSIX file "{path.resolve()}")'
        )

    def delete_permanent(self, path: Path) -> None:
        path = path.expanduser()
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


class MacClipboardController:
    name = "macos_clipboard"

    def read(self) -> str:
        result = _run(["pbpaste"], check=False)
        return result.stdout or ""

    def write(self, text: str) -> None:
        proc = subprocess.run(
            ["pbcopy"],
            input=text,
            text=True,
            check=True,
            capture_output=True,
        )
        _ = proc


class MacWindowController:
    name = "macos_window"

    def list_windows(self) -> list[str]:
        script = (
            'tell application "System Events" to get name of every process '
            "whose background only is false"
        )
        out = _osascript(script)
        if not out:
            return []
        return [x.strip() for x in out.split(",") if x.strip()]

    def focus(self, title_or_app: str) -> None:
        _osascript(f'tell application "{title_or_app}" to activate')

    def minimize(self, title_or_app: str | None = None) -> None:
        if title_or_app:
            _osascript(
                f'tell application "System Events" to set visible of '
                f'process "{title_or_app}" to false'
            )
        else:
            _osascript(
                'tell application "System Events" to keystroke "m" '
                "using {command down}"
            )


class MacKeyboardController:
    name = "macos_keyboard"

    def type_text(self, text: str) -> None:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        _osascript(
            f'tell application "System Events" to keystroke "{escaped}"'
        )

    def hotkey(self, *keys: str) -> None:
        # keys: "c", "command" → command+c
        mapping = {
            "command": "command down",
            "cmd": "command down",
            "shift": "shift down",
            "option": "option down",
            "alt": "option down",
            "control": "control down",
            "ctrl": "control down",
        }
        mods = [mapping[k.lower()] for k in keys[:-1] if k.lower() in mapping]
        key = keys[-1]
        if mods:
            using = ", ".join(mods)
            _osascript(
                f'tell application "System Events" to keystroke "{key}" '
                f"using {{{using}}}"
            )
        else:
            _osascript(
                f'tell application "System Events" to keystroke "{key}"'
            )


class MacMouseController:
    name = "macos_mouse"

    def click(self, x: int, y: int, button: str = "left") -> None:
        # Usa cliclick si existe; si no, AppleScript limitado
        if shutil.which("cliclick"):
            btn = "c" if button == "left" else "rc"
            _run(["cliclick", f"{btn}:{x},{y}"])
            return
        _LOG.warning("cliclick_missing", hint="brew install cliclick")
        _osascript(
            f'tell application "System Events" to click at {{{x}, {y}}}'
        )

    def move(self, x: int, y: int) -> None:
        if shutil.which("cliclick"):
            _run(["cliclick", f"m:{x},{y}"])
            return
        _LOG.warning("cliclick_missing_move")


class MacShellController:
    name = "macos_shell"

    DEFAULT_ALLOW = {
        "ls",
        "pwd",
        "echo",
        "date",
        "whoami",
        "uname",
        "df",
        "du",
        "cat",
        "head",
        "tail",
        "wc",
        "which",
        "brew",
        "git",
        "python3",
        "poetry",
        "ollama",
    }

    def __init__(self, allowlist: set[str] | None = None) -> None:
        self.allowlist = allowlist or set(self.DEFAULT_ALLOW)

    _SHELL_META = (";", "&&", "||", "|", "`", "$(", "${", ">", "<", "&", "\n")

    def run(self, command: str, *, allowed: bool = False) -> tuple[int, str, str]:
        cmd = command.strip()
        if not cmd:
            return 0, "", ""
        if any(tok in cmd for tok in self._SHELL_META):
            raise PermissionError('Solo se permite un comando simple sin tuberías, redirecciones ni encadenamiento.')
        try:
            argv = shlex.split(cmd)
        except ValueError as exc:
            raise PermissionError(f'Comando mal formado: {exc}') from exc
        if not argv:
            return 0, "", ""
        base = Path(argv[0]).name
        if not allowed and base not in self.allowlist:
            raise PermissionError(f'Comando no permitido: {base}. Permitidos: {", ".join(sorted(self.allowlist))}')
        result = subprocess.run(argv, shell=False, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout or "", result.stderr or ""

class MacScreenshotController:
    name = "macos_screenshot"

    def __init__(self, default_dir: Path | None = None) -> None:
        self.default_dir = default_dir

    def capture(self, path: Path | None = None) -> Path:
        from datetime import datetime

        if path is None:
            base = self.default_dir or (Path.home() / "Desktop")
            base.mkdir(parents=True, exist_ok=True)
            path = base / f"jarvis-shot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _run(["screencapture", "-x", str(path)])
        except subprocess.CalledProcessError:
            # Fallback: captura interactiva desactivada; intenta /tmp
            alt = Path("/tmp") / path.name
            _run(["screencapture", "-x", str(alt)])
            if alt.exists() and alt != path:
                path.write_bytes(alt.read_bytes())
        if not path.exists():
            raise RuntimeError(
                "No se pudo capturar la pantalla. "
                "Concede a Terminal/Cursor el permiso de Grabación de pantalla "
                "en Ajustes del Sistema → Privacidad."
            )
        return path
