#!/usr/bin/env python3
"""extract_css.py — Extract design parameters from a website's CSS.

Usage:
    python extract_css.py <URL>

Output:
    JSON to stdout containing:
      - colors: top hex colors with frequencies
      - background_colors: top background hex colors
      - text_colors: top text colors
      - fonts: unique font-family declarations
      - font_sizes: unique font-size declarations (sorted)
      - border_radius: unique border-radius values with frequencies
      - box_shadows: unique box-shadow values with frequencies
      - transitions: unique transition values with frequencies
      - breakpoints: unique @media breakpoints

The downstream agent (Claude) takes this JSON and fills out the DESIGN.md template.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    sys.stderr.write("ERROR: requests is required. Install with `pip install requests`.\n")
    sys.exit(1)


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def find_css_urls(html: str, base_url: str) -> list[str]:
    pattern = re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', re.IGNORECASE)
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    urls: list[str] = []
    for tag in pattern.findall(html):
        m = href_pattern.search(tag)
        if m:
            urls.append(urljoin(base_url, m.group(1)))
    return urls


def collect_css(html: str, base_url: str) -> str:
    parts: list[str] = []
    inline_pattern = re.compile(r"<style[^>]*>([\s\S]*?)</style>", re.IGNORECASE)
    parts.extend(inline_pattern.findall(html))
    for css_url in find_css_urls(html, base_url):
        try:
            parts.append(fetch(css_url))
        except Exception as exc:
            sys.stderr.write(f"WARN: failed to fetch {css_url}: {exc}\n")
    return "\n".join(parts)


def normalize_hex(value: str) -> str:
    value = value.lower()
    if len(value) == 4:  # expand #abc -> #aabbcc
        return "#" + "".join(c * 2 for c in value[1:])
    return value


def top_counter(values: list[str], limit: int = 12) -> list[dict]:
    counter = Counter(values)
    return [{"value": v, "count": c} for v, c in counter.most_common(limit)]


def extract(css: str) -> dict:
    hex_re = re.compile(r"#[0-9a-fA-F]{3,6}\b")
    bg_re = re.compile(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})")
    color_re = re.compile(r"(?<![-\w])color\s*:\s*(#[0-9a-fA-F]{3,6})")
    font_family_re = re.compile(r"font-family\s*:\s*([^;}]+)")
    font_size_re = re.compile(r"font-size\s*:\s*([^;}]+)")
    radius_re = re.compile(r"border-radius\s*:\s*([^;}]+)")
    shadow_re = re.compile(r"box-shadow\s*:\s*([^;}]+)")
    transition_re = re.compile(r"transition\s*:\s*([^;}]+)")
    media_re = re.compile(r"@media\s+([^{]+)\{")

    all_hex = [normalize_hex(h) for h in hex_re.findall(css)]
    bg_hex = [normalize_hex(h) for h in bg_re.findall(css)]
    text_hex = [normalize_hex(h) for h in color_re.findall(css)]

    fonts = sorted({f.strip() for f in font_family_re.findall(css)})
    font_sizes = sorted({s.strip() for s in font_size_re.findall(css)})
    radii = [r.strip() for r in radius_re.findall(css)]
    shadows = [s.strip() for s in shadow_re.findall(css)]
    transitions = [t.strip() for t in transition_re.findall(css)]
    breakpoints = sorted({m.strip() for m in media_re.findall(css)})

    return {
        "colors_top": top_counter(all_hex, 15),
        "background_colors_top": top_counter(bg_hex, 10),
        "text_colors_top": top_counter(text_hex, 10),
        "fonts": fonts,
        "font_sizes": font_sizes,
        "border_radius_top": top_counter(radii, 10),
        "box_shadows_top": top_counter(shadows, 8),
        "transitions_top": top_counter(transitions, 8),
        "breakpoints": breakpoints,
    }


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: extract_css.py <URL>\n")
        return 1
    url = sys.argv[1]
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    if not parsed.netloc:
        sys.stderr.write(f"ERROR: invalid URL: {url}\n")
        return 1

    try:
        html = fetch(url)
    except Exception as exc:
        sys.stderr.write(f"ERROR: failed to fetch {url}: {exc}\n")
        return 1

    css = collect_css(html, url)
    if not css.strip():
        sys.stderr.write("WARN: no CSS found (inline or linked).\n")

    result = {
        "source_url": url,
        "css_length": len(css),
        **extract(css),
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
