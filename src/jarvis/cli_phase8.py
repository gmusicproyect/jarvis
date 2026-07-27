"""CLI Fase 8 — plugins, models, backup, autostart."""

from __future__ import annotations

from pathlib import Path

from jarvis.config import clear_config_cache, get_config, project_root
from jarvis.utils.logging import setup_logging


def cmd_plugins(args) -> int:  # noqa: ANN001
    from jarvis.plugins.manager import PluginManager

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    pm = PluginManager(project_root() / "plugins")
    action = args.plugins_action
    if action == "list":
        items = pm.list_installed()
        if not items:
            print("(sin plugins instalados)")
            return 0
        for p in items:
            flag = "on" if p.enabled else "off"
            err = f" ERR={';'.join(p.errors)}" if p.errors else ""
            print(
                f"- {p.manifest.name} v{p.manifest.version} [{flag}] "
                f"— {p.manifest.description}{err}"
            )
        return 0
    if action == "install":
        plug = pm.install(args.target)
        print(f"Instalado: {plug.manifest.name} v{plug.manifest.version}")
        return 0
    if action == "enable":
        pm.enable(args.target)
        print(f"Activado: {args.target}")
        return 0
    if action == "disable":
        pm.disable(args.target)
        print(f"Desactivado: {args.target}")
        return 0
    if action == "remove":
        pm.remove(args.target)
        print(f"Eliminado: {args.target}")
        return 0
    print(f"Acción desconocida: {action}")
    return 1


def cmd_models(args) -> int:  # noqa: ANN001
    from jarvis.models.manager import ModelManager

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    mm = ModelManager(cfg.llm.base_url)
    action = args.models_action
    if action == "list":
        try:
            models = mm.list()
        except Exception as exc:  # noqa: BLE001
            print(f"No pude listar modelos (¿Ollama activo?): {exc}")
            return 1
        if not models:
            print("(ningún modelo en Ollama)")
            return 0
        for m in models:
            print(f"- {m.name:30} {m.kind:10} {m.size_gb:.2f} GB")
        return 0
    if action == "pull":
        print(mm.pull(args.name))
        return 0
    if action == "remove":
        print(mm.remove(args.name))
        return 0
    return 1


def cmd_backup(args) -> int:  # noqa: ANN001
    from jarvis.backup.manager import BackupManager

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    bm = BackupManager()
    action = args.backup_action
    if action == "create":
        path = bm.create(label=getattr(args, "label", None))
        print(f"Backup creado: {path}")
        return 0
    if action == "restore":
        bm.restore(Path(args.path), force=bool(getattr(args, "force", False)))
        print(f"Restaurado desde: {args.path}")
        return 0
    if action == "list":
        for p in bm.list_backups():
            print(f"- {p}")
        return 0
    return 1


def cmd_autostart(args) -> int:  # noqa: ANN001
    from jarvis.platform.autostart import install_autostart, uninstall_autostart

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    if args.autostart_action == "install":
        path = install_autostart(minimized=not args.full)
        print(f"Autostart instalado: {path}")
        return 0
    if args.autostart_action == "uninstall":
        uninstall_autostart()
        print("Autostart eliminado.")
        return 0
    return 1


def add_phase8_parsers(sub) -> None:  # noqa: ANN001
    p_plugins = sub.add_parser("plugins", help="Gestiona plugins")
    p_plugins_sub = p_plugins.add_subparsers(dest="plugins_action", required=True)
    p_plugins_sub.add_parser("list", help="Lista plugins instalados")
    p_in = p_plugins_sub.add_parser("install", help="Instala desde carpeta local")
    p_in.add_argument("target", help="Ruta al plugin o nombre marketplace")
    p_en = p_plugins_sub.add_parser("enable", help="Activa un plugin")
    p_en.add_argument("target")
    p_dis = p_plugins_sub.add_parser("disable", help="Desactiva un plugin")
    p_dis.add_argument("target")
    p_rm = p_plugins_sub.add_parser("remove", help="Elimina un plugin")
    p_rm.add_argument("target")

    p_models = sub.add_parser("models", help="Gestiona modelos Ollama")
    p_models_sub = p_models.add_subparsers(dest="models_action", required=True)
    p_models_sub.add_parser("list", help="Lista modelos instalados")
    p_pull = p_models_sub.add_parser("pull", help="Descarga un modelo")
    p_pull.add_argument("name")
    p_del = p_models_sub.add_parser("remove", help="Elimina un modelo")
    p_del.add_argument("name")

    p_backup = sub.add_parser("backup", help="Backup y restauración")
    p_backup_sub = p_backup.add_subparsers(dest="backup_action", required=True)
    p_bc = p_backup_sub.add_parser("create", help="Crea un backup")
    p_bc.add_argument("--label", default=None)
    p_br = p_backup_sub.add_parser("restore", help="Restaura un backup")
    p_br.add_argument("path")
    p_br.add_argument("--force", action="store_true")
    p_backup_sub.add_parser("list", help="Lista backups")

    p_auto = sub.add_parser("autostart", help="Inicio automático con el sistema")
    p_auto_sub = p_auto.add_subparsers(dest="autostart_action", required=True)
    p_ai = p_auto_sub.add_parser("install", help="Instala autostart")
    p_ai.add_argument(
        "--full",
        action="store_true",
        help="Arranca loop de voz en lugar de GUI",
    )
    p_auto_sub.add_parser("uninstall", help="Quita autostart")
