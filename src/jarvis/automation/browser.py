"""BrowserController con Playwright (lazy import)."""

from __future__ import annotations

import urllib.parse
from pathlib import Path

from jarvis.utils.logging import get_logger


class PlaywrightBrowserController:
    """Proveedor de navegador basado en Playwright.

    Requiere: ``poetry add playwright`` y ``poetry run playwright install chromium``.
    Si no está instalado, open_url cae a ``open`` del sistema.
    """

    name = "playwright"

    def __init__(self, *, headless: bool = False, timeout_ms: int = 30000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._log = get_logger("jarvis.automation.browser")
        self._playwright = None
        self._browser = None
        self._page = None

    def _ensure(self) -> None:
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright no instalado. Ejecuta: poetry add playwright "
                "&& poetry run playwright install chromium"
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        self._page.set_default_timeout(self.timeout_ms)

    def open_url(self, url: str) -> None:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            self._ensure()
            assert self._page is not None
            self._page.goto(url, wait_until="domcontentloaded")
        except RuntimeError:
            # fallback sistema
            import subprocess

            subprocess.run(["open", url], check=True)
            self._log.warning("playwright_fallback_open", url=url)

    def search_google(self, query: str) -> None:
        q = urllib.parse.quote_plus(query)
        self.open_url(f"https://www.google.com/search?q={q}")

    def click(self, selector: str) -> None:
        self._ensure()
        assert self._page is not None
        self._page.click(selector)

    def fill(self, selector: str, text: str) -> None:
        self._ensure()
        assert self._page is not None
        self._page.fill(selector, text)

    def get_page_text(self) -> str:
        self._ensure()
        assert self._page is not None
        return self._page.inner_text("body")

    def extract_tables(self) -> list[list[list[str]]]:
        self._ensure()
        assert self._page is not None
        return self._page.evaluate(
            """() => Array.from(document.querySelectorAll('table')).map(t =>
              Array.from(t.querySelectorAll('tr')).map(tr =>
                Array.from(tr.querySelectorAll('th,td')).map(c => c.innerText.trim())
              )
            )"""
        )

    def screenshot(self, path: Path) -> Path:
        self._ensure()
        assert self._page is not None
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=True)
        return path

    def download(self, url: str, dest: Path) -> Path:
        import httpx

        dest = dest.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        return dest

    def close(self) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
            if self._playwright is not None:
                self._playwright.stop()
        finally:
            self._browser = None
            self._playwright = None
            self._page = None


class SystemOpenBrowserController:
    """Fallback: abre URL con el navegador por defecto del SO."""

    name = "system_open"

    def open_url(self, url: str) -> None:
        import subprocess

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        subprocess.run(["open", url], check=True)

    def search_google(self, query: str) -> None:
        import urllib.parse

        q = urllib.parse.quote_plus(query)
        self.open_url(f"https://www.google.com/search?q={q}")

    def click(self, selector: str) -> None:
        raise NotImplementedError("system_open no soporta click")

    def fill(self, selector: str, text: str) -> None:
        raise NotImplementedError("system_open no soporta fill")

    def get_page_text(self) -> str:
        raise NotImplementedError("system_open no soporta get_page_text")

    def extract_tables(self) -> list[list[list[str]]]:
        raise NotImplementedError("system_open no soporta extract_tables")

    def screenshot(self, path: Path) -> Path:
        raise NotImplementedError("system_open no soporta screenshot de página")

    def download(self, url: str, dest: Path) -> Path:
        import httpx

        dest = dest.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        return dest

    def close(self) -> None:
        return None
