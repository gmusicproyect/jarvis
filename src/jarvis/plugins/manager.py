"""Plugin Manager — instalar, activar, validar, cargar skills."""

from __future__ import annotations

import importlib.util
import inspect
import json
import shutil
from pathlib import Path

from jarvis.config.loader import project_root
from jarvis.plugins.manifest import InstalledPlugin, PluginManifest, load_manifest
from jarvis.plugins.marketplace import StubMarketplace
from jarvis.skills.skill import Skill
from jarvis.utils.logging import get_logger

KNOWN_PERMISSIONS = {
    "safe",
    "confirm",
    "restricted",
    "audio_control",
    "filesystem",
    "network",
    "browser",
    "shell",
    "vision",
    "notifications",
}


class PluginManager:
    def __init__(
        self,
        plugins_dir: Path | None = None,
        *,
        state_path: Path | None = None,
    ) -> None:
        root = project_root()
        self.plugins_dir = plugins_dir or (root / "plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = state_path or (root / "data" / "plugins_state.json")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.marketplace = StubMarketplace()
        self._log = get_logger("jarvis.plugins")
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"enabled": {}, "disabled": []}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {"enabled": {}, "disabled": []}

    def _save_state(self) -> None:
        self.state_path.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_installed(self) -> list[InstalledPlugin]:
        found: list[InstalledPlugin] = []
        for child in sorted(self.plugins_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            manifest_path = child / "manifest.yaml"
            if not manifest_path.exists():
                continue
            try:
                manifest = load_manifest(manifest_path)
            except Exception as exc:  # noqa: BLE001
                found.append(
                    InstalledPlugin(
                        PluginManifest(name=child.name),
                        child,
                        enabled=False,
                        errors=[str(exc)],
                    )
                )
                continue
            disabled = set(self._state.get("disabled", []))
            enabled = manifest.name not in disabled and manifest.enabled
            errors = self.validate(manifest)
            found.append(
                InstalledPlugin(manifest, child, enabled=enabled, errors=errors)
            )
        return found

    def validate(self, manifest: PluginManifest) -> list[str]:
        errors: list[str] = []
        for perm in manifest.permissions:
            if perm not in KNOWN_PERMISSIONS:
                errors.append(f"permiso desconocido: {perm}")
        if not manifest.name:
            errors.append("name vacío")
        return errors

    def install(self, source: str) -> InstalledPlugin:
        """Instala desde carpeta local o nombre (marketplace stub)."""
        src = Path(source).expanduser()
        if src.exists() and src.is_dir():
            return self._install_from_dir(src)
        # intentar marketplace
        try:
            self.marketplace.fetch(source)
        except NotImplementedError as exc:
            raise FileNotFoundError(
                f"No encontré el plugin '{source}'. "
                "Pasa una carpeta local con manifest.yaml."
            ) from exc
        raise FileNotFoundError(source)

    def _install_from_dir(self, src: Path) -> InstalledPlugin:
        manifest_path = src / "manifest.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Falta manifest.yaml en {src}")
        manifest = load_manifest(manifest_path)
        errors = self.validate(manifest)
        if errors:
            raise ValueError("Manifest inválido: " + "; ".join(errors))
        dest = self.plugins_dir / manifest.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        # asegurar estructura mínima
        for name in ("README.md", "config.yaml"):
            p = dest / name
            if not p.exists():
                p.write_text(
                    f"# {manifest.name}\n" if name.endswith(".md") else "{}\n",
                    encoding="utf-8",
                )
        tests = dest / "tests"
        tests.mkdir(exist_ok=True)
        self._state.setdefault("enabled", {})[manifest.name] = True
        if manifest.name in self._state.get("disabled", []):
            self._state["disabled"].remove(manifest.name)
        self._save_state()
        self._log.info("plugin_installed", name=manifest.name, path=str(dest))
        return InstalledPlugin(manifest, dest, enabled=True)

    def enable(self, name: str) -> None:
        disabled = set(self._state.get("disabled", []))
        disabled.discard(name)
        self._state["disabled"] = sorted(disabled)
        self._state.setdefault("enabled", {})[name] = True
        self._save_state()
        self._log.info("plugin_enabled", name=name)

    def disable(self, name: str) -> None:
        disabled = set(self._state.get("disabled", []))
        disabled.add(name)
        self._state["disabled"] = sorted(disabled)
        self._save_state()
        self._log.info("plugin_disabled", name=name)

    def remove(self, name: str) -> None:
        dest = self.plugins_dir / name
        if dest.exists():
            shutil.rmtree(dest)
        self.disable(name)
        self._state.get("enabled", {}).pop(name, None)
        self._save_state()
        self._log.info("plugin_removed", name=name)

    def load_skills(self) -> list[Skill]:
        """Carga skills de plugins habilitados (para SkillManager)."""
        skills: list[Skill] = []
        for plugin in self.list_installed():
            if not plugin.enabled or plugin.errors:
                continue
            entry = plugin.path / plugin.manifest.entry
            if not entry.exists():
                # buscar cualquier .py no test
                pys = [
                    p
                    for p in plugin.path.glob("*.py")
                    if not p.name.startswith("_")
                ]
                if not pys:
                    continue
                entry = pys[0]
            skills.extend(self._load_skills_from_file(entry, plugin.manifest.name))
        return skills

    def _load_skills_from_file(self, path: Path, plugin_name: str) -> list[Skill]:
        spec = importlib.util.spec_from_file_location(
            f"jarvis_plugin_{plugin_name}_{path.stem}", path
        )
        if spec is None or spec.loader is None:
            return []
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            self._log.warning("plugin_load_failed", plugin=plugin_name, error=str(exc))
            return []
        out: list[Skill] = []
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, Skill)
                and obj is not Skill
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                out.append(obj())
        return out
