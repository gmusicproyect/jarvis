"""Backup y restauración de datos Jarvis."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from jarvis.config.loader import project_root
from jarvis.utils.logging import get_logger

INCLUDE_GLOBS = [
    "config/config.yaml",
    ".env.example",  # no .env con secretos
    "data/db/*.db",
    "data/plugins_state.json",
    "data/chroma/**",
    "data/chroma_rag/**",
    "knowledge/**",
    "plugins/**",
]

EXCLUDE_PARTS = {
    "__pycache__",
    ".git",
    "node_modules",
    "screenshots",
    "logs",
    "emb_cache.db",
}


class BackupManager:
    def __init__(self, backup_dir: Path | None = None) -> None:
        root = project_root()
        self.root = root
        self.backup_dir = backup_dir or (root / "data" / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._log = get_logger("jarvis.backup")

    def create(self, label: str | None = None) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"jarvis-backup-{stamp}"
        if label:
            safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in label)[:40]
            name = f"{name}-{safe}"
        zip_path = self.backup_dir / f"{name}.zip"
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "label": label,
            "includes": INCLUDE_GLOBS,
            "excludes_models": True,
        }
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("backup_manifest.json", json.dumps(manifest, indent=2))
            for rel in self._collect_files():
                abs_path = self.root / rel
                if abs_path.is_file():
                    zf.write(abs_path, arcname=str(rel))
        self._log.info("backup_created", path=str(zip_path))
        return zip_path

    def _collect_files(self) -> list[Path]:
        files: list[Path] = []
        # explícitos
        for pattern in (
            "config/config.yaml",
            "data/plugins_state.json",
        ):
            p = self.root / pattern
            if p.exists():
                files.append(Path(pattern))
        # dbs
        db_dir = self.root / "data" / "db"
        if db_dir.exists():
            for p in db_dir.glob("*.db"):
                if p.name == "emb_cache.db":
                    continue
                files.append(p.relative_to(self.root))
        # chroma (sin temporales enormes si no existen)
        for chroma in ("data/chroma", "data/chroma_rag"):
            base = self.root / chroma
            if base.exists():
                for p in base.rglob("*"):
                    if p.is_file() and not any(part in EXCLUDE_PARTS for part in p.parts):
                        files.append(p.relative_to(self.root))
        # knowledge + plugins
        for folder in ("knowledge", "plugins"):
            base = self.root / folder
            if base.exists():
                for p in base.rglob("*"):
                    if p.is_file() and not any(part in EXCLUDE_PARTS for part in p.parts):
                        files.append(p.relative_to(self.root))
        # unique
        return sorted(set(files))

    def restore(self, zip_path: Path, *, force: bool = False) -> Path:
        zip_path = zip_path.expanduser().resolve()
        if not zip_path.exists():
            raise FileNotFoundError(zip_path)
        # backup de seguridad previo
        if not force:
            self.create(label="pre-restore")
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir() or info.filename == "backup_manifest.json":
                    continue
                # no sobrescribir .env
                if info.filename.endswith(".env"):
                    continue
                target = self.root / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        self._log.info("backup_restored", path=str(zip_path))
        return self.root

    def list_backups(self) -> list[Path]:
        return sorted(self.backup_dir.glob("jarvis-backup-*.zip"), reverse=True)
