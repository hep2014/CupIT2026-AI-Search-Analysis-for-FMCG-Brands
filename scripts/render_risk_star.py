from __future__ import annotations

import math
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


TEMPLATE_DIR = Path("templates")
TEMPLATE_NAME = "risk_star.html.j2"

OUT_DIR = Path("out")
OUT_HTML = OUT_DIR / "risk_star.html"
OUT_PNG = OUT_DIR / "risk_star.png"
OUT_PDF = OUT_DIR / "risk_star.pdf"


risk_matrix = [
    {
        "risk": "Изменение алгоритмов AI-поиска",
        "probability": "medium",
        "impact": "high",
        "description": "AI-платформы могут изменить логику формирования ответов и источников."
    },
    {
        "risk": "Низкая индексация нового контента",
        "probability": "medium",
        "impact": "medium",
        "description": "Контент может медленно попадать в источники, используемые AI."
    },
    {
        "risk": "Рост активности конкурентов",
        "probability": "high",
        "impact": "medium",
        "description": "Конкуренты могут начать аналогичную оптимизацию AI-поиска."
    },
    {
        "risk": "Низкая эффективность размещений на внешних доменах",
        "probability": "medium",
        "impact": "medium",
        "description": "Некоторые источники могут не попадать в AI-ответы."
    },
    {
        "risk": "Ошибки мониторинга AI-ответов",
        "probability": "low",
        "impact": "medium",
        "description": "Некорректный сбор данных может влиять на аналитику."
    },
    {
        "risk": "Недостаточный объем контента",
        "probability": "low",
        "impact": "high",
        "description": "Недостаточный охват запросов может снизить эффект стратегии."
    }
]

SUMMARY_TEXT = [
    "Внедрение стратегии оптимизации под AI-поиск сопровождается рядом технологических и рыночных рисков. Наиболее значимыми являются изменения алгоритмов AI-поисковых систем и возможная активизация конкурентов в данной области.",
    "Тем не менее большинство рисков имеет среднюю вероятность и управляемый характер, поскольку стратегия предполагает постоянный мониторинг AI-ответов, адаптацию контента и диверсификацию источников присутствия бренда.",
    "Таким образом, риски проекта оцениваются как контролируемые, а ожидаемый экономический эффект значительно превышает потенциальные негативные сценарии.",
]


PROB_SCORE = {"low": 1, "medium": 2, "high": 3}
IMPACT_SCORE = {"low": 1, "medium": 2, "high": 3}
PROB_LABEL = {"low": "Низкая", "medium": "Средняя", "high": "Высокая"}
IMPACT_LABEL = {"low": "Низкое", "medium": "Среднее", "high": "Высокое"}


def level_class(probability: str, impact: str) -> str:
    score = PROB_SCORE[probability] * IMPACT_SCORE[impact]
    if score >= 6:
        return "critical"
    if score >= 4:
        return "elevated"
    return "controlled"


def level_label(probability: str, impact: str) -> str:
    score = PROB_SCORE[probability] * IMPACT_SCORE[impact]
    if score >= 6:
        return "Ключевой риск"
    if score >= 4:
        return "Зона внимания"
    return "Контролируемый"


def impact_radius(impact: str) -> int:
    return {"low": 150, "medium": 220, "high": 290}[impact]


def node_radius(probability: str) -> int:
    return {"low": 18, "medium": 26, "high": 34}[probability]


def prepare_risks(raw_risks: list[dict]) -> list[dict]:
    cx, cy = 420, 360
    prepared = []
    total = len(raw_risks)

    for idx, item in enumerate(raw_risks):
        angle_deg = -90 + idx * (360 / total)
        angle_rad = math.radians(angle_deg)

        radius = impact_radius(item["impact"])
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)

        prob = item["probability"]
        imp = item["impact"]

        prepared.append(
            {
                "index": idx + 1,
                "risk": item["risk"],
                "description": item["description"],
                "probability": PROB_LABEL[prob],
                "impact": IMPACT_LABEL[imp],
                "level_class": level_class(prob, imp),
                "level_label": level_label(prob, imp),
                "node_radius": node_radius(prob),
                "x": round(x, 2),
                "y": round(y, 2),
                "cx": cx,
                "cy": cy,
                "label_x": round(cx + (radius + 64) * math.cos(angle_rad), 2),
                "label_y": round(cy + (radius + 64) * math.sin(angle_rad), 2),
            }
        )

    return prepared


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


def render_png(html_path: Path, png_path: Path, width: int = 1920, height: int = 1180) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1920, "height": 1180},
            device_scale_factor=1,
        )
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")

        page.pdf(
            path=str(pdf_path),
            print_background=True,
            prefer_css_page_size=True,
            margin={
                "top": "10mm",
                "right": "10mm",
                "bottom": "10mm",
                "left": "10mm",
            },
        )
        browser.close()


def main() -> None:
    risks = prepare_risks(risk_matrix)

    context = {
        "page_title": "Карта рисков",
        "eyebrow": "Риски проекта",
        "main_title": "Звёздная карта рисков AI Search-инициативы",
        "subtitle": "Радиальная матрица: влияние задаёт удалённость от центра, вероятность задаёт размер узла.",
        "risks": risks,
        "summary_text": SUMMARY_TEXT,
    }

    html_text = render_html(context)
    save_html(html_text, OUT_HTML)
    render_png(OUT_HTML, OUT_PNG)
    render_pdf(OUT_HTML, OUT_PDF)

    print(f"HTML сохранён: {OUT_HTML.resolve()}")
    print(f"PNG сохранён: {OUT_PNG.resolve()}")
    print(f"PDF сохранён: {OUT_PDF.resolve()}")


if __name__ == "__main__":
    main()
