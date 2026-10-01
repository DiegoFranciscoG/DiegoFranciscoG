"""Genera las tarjetas SVG de lenguajes del README de perfil.

Lee los repositorios públicos (sin forks ni archivados) con la API REST de GitHub,
suma los bytes por lenguaje y escribe una tarjeta para tema claro y otra para oscuro.
Solo usa la biblioteca estándar. GITHUB_TOKEN es opcional: sin él la API permite
60 peticiones por hora; en GitHub Actions el token del workflow sube el límite.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

API = "https://api.github.com"
TOP_N = 8

# Colores de github-linguist para que la tarjeta coincida con la barra de lenguajes de GitHub.
LANGUAGE_COLORS = {
    "Java": "#b07219",
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "C#": "#178600",
    "Dart": "#00B4AB",
    "Kotlin": "#A97BFF",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "SCSS": "#c6538c",
    "PLpgSQL": "#336790",
    "C": "#555555",
    "C++": "#f34b7d",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
}
OTHER_COLOR = "#8b949e"

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#1f2328", "text": "#1f2328", "muted": "#59636e"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#f0f6fc", "text": "#e6edf3", "muted": "#9198a1"},
}

Fetcher = Callable[[str], object]


@dataclass(frozen=True)
class LanguageShare:
    name: str
    bytes: int
    percent: float
    repos: int
    color: str


def http_fetcher(token: str | None) -> Fetcher:
    """Devuelve una función que hace GET a la API y decodifica JSON."""

    def fetch(url: str) -> object:
        if not url.startswith(f"{API}/"):
            raise ValueError(f"URL fuera de la API de GitHub: {url}")
        request = urllib.request.Request(url)  # noqa: S310 (solo https://api.github.com, validado arriba)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("User-Agent", "profile-stats")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return json.load(response)

    return fetch


def list_public_repos(user: str, fetch: Fetcher) -> list[str]:
    """Nombres de los repos públicos propios, sin forks ni archivados, recorriendo todas las páginas."""
    names: list[str] = []
    page = 1
    while True:
        batch = fetch(f"{API}/users/{user}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        for repo in batch:
            if repo.get("fork") or repo.get("archived") or repo.get("private"):
                continue
            names.append(repo["name"])
        if len(batch) < 100:
            break
        page += 1
    return sorted(names, key=str.lower)


def collect_languages(user: str, repos: list[str], fetch: Fetcher) -> list[dict[str, int]]:
    return [dict(fetch(f"{API}/repos/{user}/{name}/languages")) for name in repos]


def aggregate(
    per_repo: list[dict[str, int]], exclude: set[str] | None = None, top_n: int = TOP_N
) -> list[LanguageShare]:
    """Suma bytes por lenguaje y agrupa todo lo que queda fuera del top en «Otros»."""
    exclude = exclude or set()
    totals: Counter[str] = Counter()
    repo_count: Counter[str] = Counter()
    for languages in per_repo:
        for name, size in languages.items():
            if name in exclude or size <= 0:
                continue
            totals[name] += size
            repo_count[name] += 1
    grand_total = sum(totals.values())
    if grand_total == 0:
        return []

    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    shares = [
        LanguageShare(name, size, 100 * size / grand_total, repo_count[name], LANGUAGE_COLORS.get(name, OTHER_COLOR))
        for name, size in ranked[:top_n]
    ]
    rest = ranked[top_n:]
    if rest:
        rest_bytes = sum(size for _, size in rest)
        shares.append(LanguageShare("Otros", rest_bytes, 100 * rest_bytes / grand_total, 0, OTHER_COLOR))
    return shares


def render_svg(shares: list[LanguageShare], repo_total: int, theme: str, updated: date) -> str:
    """Tarjeta con barra apilada y leyenda en dos columnas."""
    colors = THEMES[theme]
    width, bar_x, bar_w = 480, 24, 432
    rows = (len(shares) + 1) // 2
    height = 104 + rows * 26 + 34

    segments, x = [], float(bar_x)
    for share in shares:
        seg_w = bar_w * share.percent / 100
        segments.append(f'<rect x="{x:.2f}" y="64" width="{seg_w:.2f}" height="10" fill="{share.color}"/>')
        x += seg_w

    legend = []
    for index, share in enumerate(shares):
        col, row = index % 2, index // 2
        lx, ly = 24 + col * 220, 108 + row * 26
        detail = f"{share.percent:.1f} %"
        if share.repos:
            detail += f" · {share.repos} repo{'s' if share.repos != 1 else ''}"
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{share.color}"/>'
            f'<text x="{lx + 16}" y="{ly}" class="t">{escape(share.name)}</text>'
            f'<text x="{lx + 196}" y="{ly}" class="m" text-anchor="end">{escape(detail)}</text>'
        )

    title = f"Lenguajes en {repo_total} repositorios públicos"
    footer = f"Fuente: API REST de GitHub · actualizado {updated.isoformat()}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f'<title id="title">{escape(title)}</title>\n'
        f'<desc id="desc">{escape(", ".join(f"{s.name} {s.percent:.1f} %" for s in shares))}</desc>\n'
        '<style>text{font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif}'
        f".h{{font-size:16px;font-weight:600;fill:{colors['title']}}}"
        f".t{{font-size:13px;fill:{colors['text']}}}"
        f".m{{font-size:12px;fill:{colors['muted']}}}</style>\n"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="{colors["bg"]}" stroke="{colors["border"]}"/>\n'
        f'<text x="24" y="40" class="h">{escape(title)}</text>\n'
        f'<clipPath id="bar"><rect x="{bar_x}" y="64" width="{bar_w}" height="10" rx="5"/></clipPath>\n'
        f'<g clip-path="url(#bar)">{"".join(segments)}</g>\n'
        f"{''.join(legend)}\n"
        f'<text x="24" y="{height - 18}" class="m">{escape(footer)}</text>\n'
        "</svg>\n"
    )


def main(argv: list[str] | None = None, fetch: Fetcher | None = None, today: date | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--user", default="DiegoFranciscoG")
    parser.add_argument("--out-dir", type=Path, default=Path("assets"))
    parser.add_argument("--exclude", default="", help="Lenguajes a omitir, separados por coma")
    args = parser.parse_args(argv)

    fetch = fetch or http_fetcher(os.environ.get("GITHUB_TOKEN") or None)
    repos = list_public_repos(args.user, fetch)
    exclude = {name.strip() for name in args.exclude.split(",") if name.strip()}
    shares = aggregate(collect_languages(args.user, repos, fetch), exclude)
    if not shares:
        print("No se encontraron lenguajes; no se modifican las tarjetas.", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    updated = today or date.today()
    for theme in THEMES:
        path = args.out_dir / f"languages-{theme}.svg"
        svg = render_svg(shares, len(repos), theme, updated)
        if path.exists() and same_data(path.read_text(encoding="utf-8"), svg):
            print(f"sin cambios {path}")
            continue
        path.write_text(svg, encoding="utf-8")
        print(f"escrito {path}")
    return 0


def same_data(old_svg: str, new_svg: str) -> bool:
    """Compara dos tarjetas ignorando la línea de fecha, para no generar commits solo por el día."""

    def strip_date(svg: str) -> str:
        return "\n".join(line for line in svg.splitlines() if "actualizado" not in line)

    return strip_date(old_svg) == strip_date(new_svg)


if __name__ == "__main__":
    raise SystemExit(main())
