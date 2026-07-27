"""Factory del AutomationEngine según plataforma y config."""

from __future__ import annotations

from pathlib import Path

from jarvis.automation.audit import AutomationAudit
from jarvis.automation.browser import (
    PlaywrightBrowserController,
    SystemOpenBrowserController,
)
from jarvis.automation.engine import AutomationEngine
from jarvis.automation.gate import PermissionGate
from jarvis.automation.macos import (
    MacApplicationController,
    MacClipboardController,
    MacFileController,
    MacKeyboardController,
    MacMouseController,
    MacScreenshotController,
    MacShellController,
    MacWindowController,
)
from jarvis.config.loader import JarvisConfig, project_root
from jarvis.platform import PlatformName, detect_platform
from jarvis.utils.logging import get_logger


def _resolve(root: Path, maybe: str) -> Path:
    path = Path(maybe)
    return path if path.is_absolute() else root / path


def build_automation_engine(
    cfg: JarvisConfig,
    *,
    cancel_flag: list[bool] | None = None,
) -> AutomationEngine:
    root = project_root()
    auto = cfg.automation
    log = get_logger("jarvis.automation.factory")
    platform = detect_platform()

    gate = PermissionGate(
        allow_restricted=cfg.security.allow_restricted,
        confirm_destructive=cfg.security.confirm_destructive,
    )
    audit = AutomationAudit(_resolve(root, auto.audit_db))

    if platform == PlatformName.MACOS:
        apps = MacApplicationController()
        files = MacFileController()
        clipboard = MacClipboardController()
        windows = MacWindowController()
        keyboard = MacKeyboardController()
        mouse = MacMouseController()
        shell = MacShellController(allowlist=set(auto.shell_allowlist))
        screenshot = MacScreenshotController(
            default_dir=_resolve(root, auto.screenshots_dir)
        )
    else:
        log.warning("automation_stub_platform", platform=platform.value)
        from jarvis.automation.stubs import StubControllers

        stubs = StubControllers()
        apps = stubs.apps
        files = stubs.files
        clipboard = stubs.clipboard
        windows = stubs.windows
        keyboard = stubs.keyboard
        mouse = stubs.mouse
        shell = stubs.shell
        screenshot = stubs.screenshot

    browser: PlaywrightBrowserController | SystemOpenBrowserController
    if auto.browser_provider == "playwright":
        try:
            import playwright  # noqa: F401

            browser = PlaywrightBrowserController(headless=auto.browser_headless)
        except ImportError:
            log.warning("playwright_missing_fallback_system_open")
            browser = SystemOpenBrowserController()
    else:
        browser = SystemOpenBrowserController()

    engine = AutomationEngine(
        apps=apps,
        browser=browser,
        files=files,
        clipboard=clipboard,
        windows=windows,
        keyboard=keyboard,
        mouse=mouse,
        shell=shell,
        screenshot=screenshot,
        gate=gate,
        audit=audit,
        user_name=cfg.app.user_name,
        cancel_flag=cancel_flag,
    )
    log.info(
        "automation_ready",
        platform=platform.value,
        browser=browser.name,
        allow_restricted=cfg.security.allow_restricted,
    )
    return engine
