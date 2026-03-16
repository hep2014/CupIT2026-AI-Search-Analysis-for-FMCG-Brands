from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "intent_type_chart.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "intent_type_chart.html"
OUT_PNG = OUT_DIR / "intent_type_chart.png"


def prepare_rows(raw_rows: list[dict]) -> tuple[list[dict], int]:
    max_value = max((item["pg"] for item in raw_rows), default=1)
    prepared = []

    for item in raw_rows:
        pg_value = item["pg"]
        competitor_value = item.get("competitor", 0)

        prepared.append(
            {
                "label": item["label"],
                "pg": pg_value,
                "competitor": competitor_value,
                "pg_width_pct": (pg_value / max_value * 100) if max_value else 0.0,
                "competitor_width_pct": (competitor_value / max_value * 100) if max_value else 0.0,
            }
        )

    return prepared, max_value


def render_html(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(TEMPLATE_NAME)
    return template.render(**context)


def save_html(html_text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def render_png(html_path: Path, png_path: Path, width: int = 1600, height: int = 900) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()


def main() -> None:
    raw_rows = [
        {"label": "Бренд", "pg": 6, "competitor": 1},
        {"label": "Категория", "pg": 4, "competitor": 0},
        {"label": "Сравнение", "pg": 2, "competitor": 1},
        {"label": "Консультация", "pg": 1, "competitor": 0},
    ]

    rows, max_value = prepare_rows(raw_rows)

    context = {
        "page_title": "Intent type — P&G",
        "main_title": "Брендовый для P&G",
        "subtitle": "",
        "rows": rows,
        "max_value": max_value,
    }

    html_text = render_html(context)
    save_html(html_text, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)

    print(f"HTML сохранён: {OUT_HTML.resolve()}")
    print(f"PNG сохранён: {OUT_PNG.resolve()}")


if __name__ == "__main__":
    main()
