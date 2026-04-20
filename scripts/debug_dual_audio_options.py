#!/usr/bin/env python3
"""Diagnostico isolado de opcoes de audio/legenda em paginas comando.la."""

from __future__ import annotations

import argparse
import time
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


def _fetch_html(url: str) -> str:
    try:
        from cloakbrowser import launch_persistent_context

        profile_dir = Path.home() / ".local/share/comando-cli/cloak_profile_debug"
        profile_dir.parent.mkdir(parents=True, exist_ok=True)

        ctx = launch_persistent_context(str(profile_dir), headless=True, humanize=True)
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
            time.sleep(3)
            return page.content()
        finally:
            page.close()
            ctx.close()
    except Exception:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception:
            from scrapling import StealthyFetcher

            result = StealthyFetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                google_search=False,
                solve_cloudflare=True,
            )
            html = (
                getattr(result, "html_content", None)
                or getattr(result, "text", None)
                or ""
            )
            if not html:
                raise RuntimeError("Falha ao obter HTML com CloakBrowser/requests/StealthyFetcher")
            return html


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.upper()


def _detect_language(context_text: str) -> str:
    normalized = _normalize(context_text)

    if "DUAL" in normalized and "AUDIO" in normalized:
        return "Dual Audio"
    if "DUAL" in normalized:
        return "Dual Audio"
    if "DUBLADO" in normalized or ".DUB." in normalized:
        return "Dublado"
    if "LEGENDADO" in normalized or ".LEG." in normalized:
        return "Legendado"
    if "PORTUGUES" in normalized:
        return "Portuguese"
    if "ENGLISH" in normalized or "INGLES" in normalized:
        return "English"
    return "Unknown"


def _extract_quality(link_text: str, magnet: str) -> str:
    text = _normalize(link_text)
    for q in ["2160P", "4K", "1080P", "720P", "480P"]:
        if q in text:
            return q.replace("P", "p") if q.endswith("P") else q

    dn_match = re.search(r"dn=([^&]+)", magnet)
    if dn_match:
        dn = _normalize(unquote(dn_match.group(1)))
        for q in ["2160P", "4K", "1080P", "720P", "480P"]:
            if q in dn:
                return q.replace("P", "p") if q.endswith("P") else q
    return "Unknown"


def inspect_url(url: str) -> int:
    html = _fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    entry_content = soup.find("div", class_="entry-content")
    if not entry_content:
        print("Nenhum bloco div.entry-content encontrado.")
        return 1

    magnets = entry_content.find_all("a", href=re.compile(r"^magnet:"))
    if not magnets:
        print("Nenhum magnet link encontrado.")
        return 1

    dual_count = 0
    print(f"URL: {url}")
    print(f"Magnets encontrados: {len(magnets)}")
    print("-" * 90)

    for idx, link in enumerate(magnets, start=1):
        magnet = str(link.get("href", ""))
        link_text = link.get_text(" ", strip=True)

        parent_p = link.find_parent("p")
        p_text = parent_p.get_text(" ", strip=True) if parent_p else ""

        prev_strong = link.find_previous("strong")
        strong_text = prev_strong.get_text(" ", strip=True) if prev_strong else ""

        dn_match = re.search(r"dn=([^&]+)", magnet)
        dn = unquote(dn_match.group(1)) if dn_match else ""

        combined_context = " ".join([p_text, strong_text, dn]).strip()
        language = _detect_language(combined_context)
        quality = _extract_quality(link_text, magnet)
        is_dual = language == "Dual Audio"
        if is_dual:
            dual_count += 1

        print(f"[{idx}] quality={quality} language={language} dual={is_dual}")
        print(f"     link_text: {link_text}")
        print(f"     strong:    {strong_text or '-'}")
        print(f"     p_text:    {p_text or '-'}")
        print(f"     dn:        {dn or '-'}")
        print()

    print("-" * 90)
    print(f"Total Dual Audio: {dual_count}/{len(magnets)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspeciona opcoes de audio/legenda de magnets em uma pagina comando.la",
    )
    parser.add_argument("url", help="URL da pagina do filme/serie em comando.la")
    args = parser.parse_args()
    return inspect_url(args.url)


if __name__ == "__main__":
    raise SystemExit(main())
