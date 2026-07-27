"""CLI Fase 9 — doctor, profile, onboard, privacy."""

from __future__ import annotations

from pathlib import Path

from jarvis.config import clear_config_cache, get_config
from jarvis.utils.logging import setup_logging


def add_phase9_parsers(sub) -> None:  # noqa: ANN001
    p_doctor = sub.add_parser("doctor", help="Diagnóstico del entorno Jarvis")
    p_doctor.add_argument(
        "--json",
        action="store_true",
        help="Salida JSON",
    )

    p_profile = sub.add_parser("profile", help="Perfiles de rendimiento")
    p_prof = p_profile.add_subparsers(dest="profile_action", required=True)
    p_prof.add_parser("list", help="Lista perfiles")
    p_show = p_prof.add_parser("show", help="Muestra el perfil activo")
    _ = p_show
    p_apply = p_prof.add_parser("apply", help="Aplica un perfil")
    p_apply.add_argument(
        "name",
        choices=["performance", "balanced", "lightweight"],
        help="Nombre del perfil",
    )

    p_onboard = sub.add_parser("onboard", help="Asistente de primer inicio")
    p_onboard.add_argument(
        "--non-interactive",
        action="store_true",
        help="Usa valores por defecto (CI / smoke)",
    )
    p_onboard.add_argument("--user-name", default=None)
    p_onboard.add_argument(
        "--profile",
        default="balanced",
        choices=["performance", "balanced", "lightweight"],
    )
    p_onboard.add_argument("--skip-backup", action="store_true")
    p_onboard.add_argument(
        "--force",
        action="store_true",
        help="Ejecuta aunque onboarding_completed=true",
    )

    p_priv = sub.add_parser("privacy", help="Privacidad y datos personales")
    p_ps = p_priv.add_subparsers(dest="privacy_action", required=True)
    p_export = p_ps.add_parser("export", help="Exporta datos personales a JSON")
    p_export.add_argument("--out", default=None, help="Ruta de salida")
    p_wipe = p_ps.add_parser("wipe", help="Borra toda la memoria personal")
    p_wipe.add_argument(
        "--yes",
        action="store_true",
        help="Confirma el borrado sin preguntar",
    )
    p_wipe.add_argument(
        "--keep-name",
        action="store_true",
        help="Conserva el nombre del usuario en el perfil",
    )
    p_mode = p_ps.add_parser("mode", help="Activa/desactiva modo privacidad")
    p_mode.add_argument("state", choices=["on", "off"])


def cmd_doctor(args) -> int:  # noqa: ANN001
    import json

    from jarvis.doctor import format_report, report_as_dict, run_doctor

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    report = run_doctor(cfg)
    if args.json:
        print(json.dumps(report_as_dict(report), ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return report.exit_code()


def cmd_profile(args) -> int:  # noqa: ANN001
    from jarvis.profiles import apply_profile, current_profile_name, list_profiles

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    action = args.profile_action
    if action == "list":
        for name, desc in list_profiles():
            mark = "◀" if name == current_profile_name() else " "
            print(f"{mark} {name:12} — {desc}")
        return 0
    if action == "show":
        print(current_profile_name())
        return 0
    if action == "apply":
        profile = apply_profile(args.name)
        print(f"Perfil aplicado: {args.name}")
        print(f"  {profile['description']}")
        models = profile.get("recommended_models") or []
        if models:
            print("  Modelos recomendados:", ", ".join(models))
        return 0
    return 1


def cmd_onboard(args) -> int:  # noqa: ANN001
    from jarvis.onboarding import needs_onboarding, run_onboarding

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    if needs_onboarding() is False and not args.force:
        print("Onboarding ya completado. Usa --force para repetirlo.")
        return 0
    result = run_onboarding(
        non_interactive=args.non_interactive,
        user_name=args.user_name,
        profile=args.profile,
        skip_backup=args.skip_backup,
    )
    if result.completed:
        print(f"Onboarding OK — usuario={result.user_name} perfil={result.profile}")
        return 0
    print("Onboarding incompleto.")
    return 1


def cmd_privacy(args) -> int:  # noqa: ANN001
    from jarvis.privacy import export_personal_data, set_privacy_mode, wipe_all_memory

    clear_config_cache()
    cfg = get_config()
    setup_logging(cfg)
    action = args.privacy_action
    if action == "export":
        path = export_personal_data(
            cfg, Path(args.out) if args.out else None
        )
        print(f"Exportado: {path}")
        return 0
    if action == "wipe":
        if not args.yes:
            print("Confirma con --yes para borrar toda la memoria personal.")
            return 1
        stats = wipe_all_memory(cfg, keep_user_name=args.keep_name)
        print(
            f"Memoria borrada: items={stats['sqlite_items']} "
            f"perfil={stats['profile_keys']} chroma={stats['chroma_cleared']}"
        )
        return 0
    if action == "mode":
        set_privacy_mode(args.state == "on")
        print(f"Modo privacidad: {args.state}")
        return 0
    return 1
