import argparse
import json
from collections import Counter
from pathlib import Path


BUG_KEYWORDS = [
    "bug", "crash", "freeze", "lag", "glitch", "broken", "stuck", "error",
    "performance", "fps", "frame", "exploit", "issue"
]


def load_reviews(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_reviews(reviews: list) -> dict:
    total = len(reviews)
    positive = sum(1 for item in reviews if item.get("voted_up", False))
    negative = total - positive

    bug_hits = []
    for item in reviews:
        text = (item.get("review", "") + " " + item.get("title", "")).lower()
        if any(keyword in text for keyword in BUG_KEYWORDS):
            bug_hits.append(item)

    keyword_counter = Counter()
    for item in bug_hits:
        text = (item.get("review", "") + " " + item.get("title", "")).lower()
        for keyword in BUG_KEYWORDS:
            if keyword in text:
                keyword_counter[keyword] += 1

    return {
        "total_reviews": total,
        "positive_reviews": positive,
        "negative_reviews": negative,
        "bug_reviews": len(bug_hits),
        "top_bug_keywords": keyword_counter.most_common(10),
    }


def classify_review(item: dict) -> list[str]:
    """Assign simple thematic labels to a review for grouping."""
    text = (item.get("review", "") + " " + item.get("title", "")).lower()
    labels = []

    if any(keyword in text for keyword in BUG_KEYWORDS):
        labels.append("Баг / сбой")
    performance_words = ("lag", "fps", "frame", "performance")
    if any(keyword in text for keyword in performance_words):
        labels.append("Производительность")
    ux_words = ("control", "ui", "menu", "tutorial", "interface")
    if any(keyword in text for keyword in ux_words):
        labels.append("UX / интерфейс")
    positive_words = ("good", "great", "love", "fun", "recommend", "best")
    if any(keyword in text for keyword in positive_words):
        labels.append("Позитив")
    if not labels:
        labels.append("Общее впечатление")

    return labels


def make_russian_summary(item: dict) -> str:
    """Create a short Russian summary for each review."""
    text = (item.get("review", "") or "").strip()
    title = (item.get("title", "") or "").strip()
    sentiment = "положительный" if item.get("voted_up") else "негативный"

    if not text and not title:
        return "Пустой отзыв без текста."

    summary = f"Это {sentiment} отзыв."
    if any(keyword in text.lower() for keyword in BUG_KEYWORDS):
        summary += " В нём упоминаются проблемы, сбои или баги."
    performance_words = ("lag", "fps", "frame", "performance")
    if any(keyword in text.lower() for keyword in performance_words):
        summary += " Есть замечания по производительности."
    ux_words = ("control", "ui", "menu", "tutorial")
    if any(keyword in text.lower() for keyword in ux_words):
        summary += " Есть замечания к интерфейсу или управлению."

    return summary


def build_markdown_report(reviews: list, input_path: Path) -> str:
    """Build a markdown report with grouped classification and review links."""
    report = summarize_reviews(reviews)
    grouped = Counter()
    for item in reviews:
        for label in classify_review(item):
            grouped[label] += 1

    lines = [
        "# Отчёт по отзывам Steam",
        "",
        f"Источник: `{input_path.name}`",
        "",
        "## Краткая сводка",
        "",
        f"- Всего отзывов: {report['total_reviews']}",
        f"- Положительных: {report['positive_reviews']}",
        f"- Негативных: {report['negative_reviews']}",
        f"- Отзывов с упоминанием багов/проблем: {report['bug_reviews']}",
        "",
        "## Быстрая навигация",
        "",
        "- [Обзор по группам](#обзор-по-группам)",
        "- [Все отзывы](#все-отзывы)",
        "",
        "## Обзор по группам",
        "",
    ]

    for label, count in grouped.most_common():
        lines.append(f"- {label}: {count} отзыв(ов)")
    lines.extend(["", "## Навигация по отзывам", ""])
    for index in range(1, len(reviews) + 1):
        lines.append(f"- [Отзыв {index}](#review-{index})")
    lines.extend(["", "## Все отзывы", ""])

    for index, item in enumerate(reviews, start=1):
        anchor = f"review-{index}"
        rating = "Позитивный" if item.get("voted_up") else "Негативный"
        labels = ", ".join(classify_review(item))
        lines.extend([
            f"<a id=\"{anchor}\"></a>",
            f"### Отзыв {index} — {rating}",
            "",
            f"- Классификация: {labels}",
            f"- Дата: {item.get('timestamp_created', '—')}",
            "- Полезность: "
            f"{item.get('votes_up', 0)} 👍 / {item.get('votes_funny', 0)} 😄",
            "",
            "**Краткий русский комментарий**",
            "",
            f"{make_russian_summary(item)}",
            "",
            "**Оригинальный текст**",
            "",
            f"> {item.get('review', '—').replace(chr(10), chr(10) + '> ')}",
            "",
            "**Заголовок**",
            "",
            f"{item.get('title', '—')}",
            "",
            "---",
            "",
        ])

    lines.append("\n## Ключевые темы")
    lines.append("")
    for keyword, count in report['top_bug_keywords']:
        lines.append(f"- {keyword}: {count}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Steam reviews")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a raw reviews JSON file",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output markdown path. Defaults to reports/<input>.md",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    reviews = load_reviews(input_path)
    report = summarize_reviews(reviews)

    output_path = (
        Path(args.output)
        if args.output
        else Path("reports") / f"{input_path.stem}.md"
    )
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(
        build_markdown_report(reviews, input_path),
        encoding="utf-8",
    )

    print("Review report")
    print("=============")
    print(f"Total reviews: {report['total_reviews']}")
    print(f"Positive: {report['positive_reviews']}")
    print(f"Negative: {report['negative_reviews']}")
    print(f"Reviews mentioning bugs/issues: {report['bug_reviews']}")
    print("Top bug keywords:")
    for keyword, count in report['top_bug_keywords']:
        print(f"  - {keyword}: {count}")

    print(f"Markdown report saved to {output_path}")


if __name__ == "__main__":
    main()
