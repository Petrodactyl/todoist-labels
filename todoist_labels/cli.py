"""Пошук релевантних міток Todoist за текстом контексту.

Два види пошуку (як у оригінальному Colab-ноутбуці):
  * нечіткий (thefuzz, partial_ratio) по очищених ключових словах;
  * семантичний (sentence-transformers) по повному тексту — опційно.
"""
import argparse
from functools import lru_cache
import os
import re
import sys

SEMANTIC_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def get_clean_keywords(text, min_length=4):
    words = re.findall(r"\w+", text.lower())
    return [w for w in words if len(w) >= min_length]


def flatten(items):
    for item in items:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item


def fetch_labels(token):
    from todoist_api_python.api import TodoistAPI

    api = TodoistAPI(token)
    return [
        {"id": l.id, "name": l.name, "color": getattr(l, "color", ""),
         "favorite": getattr(l, "is_favorite", False)}
        for l in flatten(api.get_labels())
    ]


def fuzzy_search(labels, queries, threshold=60):
    """Ранжує за кількістю різних ключових слів, що збіглись, далі за сумою оцінок."""
    from thefuzz import fuzz

    rows = []
    for label in labels:
        hits = [(q, fuzz.partial_ratio(q, label["name"])) for q in dict.fromkeys(queries)]
        hits = [(q, sc) for q, sc in hits if sc >= threshold]
        if hits:
            rows.append({**label,
                         "query": ", ".join(q for q, _ in hits),
                         "hits": len(hits),
                         "score": max(sc for _, sc in hits),
                         "total": sum(sc for _, sc in hits)})
    return sorted(rows, key=lambda r: (r["hits"], r["total"], -len(r["name"])), reverse=True)


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(SEMANTIC_MODEL)


def semantic_search(labels, text):
    from sentence_transformers import util

    model = get_model()
    query = model.encode(text, convert_to_tensor=True)
    names = model.encode([l["name"] for l in labels], convert_to_tensor=True)
    scores = util.pytorch_cos_sim(query, names)[0].cpu().numpy() * 100
    rows = [{**l, "score": float(s)} for l, s in zip(labels, scores)]
    return sorted(rows, key=lambda r: r["score"], reverse=True)


def print_table(rows, title, extra=None):
    print(f"\n{title}")
    if not rows:
        print("  (нічого не знайдено)")
        return
    for r in rows:
        tail = f"  ← {r[extra]}" if extra else ""
        print(f"  {r['score']:6.1f}  {r['name']}{tail}")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="todoist-labels",
        description="Знайти мітки Todoist, релевантні тексту контексту.")
    p.add_argument("text", nargs="*", help="текст контексту (або stdin / --file)")
    p.add_argument("-f", "--file", help="прочитати контекст із файлу")
    p.add_argument("-n", "--limit", type=int, default=20, help="скільки результатів показувати (20)")
    p.add_argument("-t", "--threshold", type=int, default=60, help="поріг нечіткого пошуку (60)")
    p.add_argument("--min-length", type=int, default=4, help="мін. довжина ключового слова (4)")
    p.add_argument("--no-semantic", action="store_true", help="пропустити семантичний пошук (швидше, без torch)")
    p.add_argument("--no-fuzzy", action="store_true", help="пропустити нечіткий пошук (корисно для текстів іншою мовою)")
    args = p.parse_args(argv)
    if args.no_fuzzy and args.no_semantic:
        p.error("--no-fuzzy і --no-semantic разом вимикають обидва пошуки")

    if args.file:
        text = open(args.file, encoding="utf-8").read()
    elif args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        p.error("потрібен текст контексту (аргумент, --file або stdin)")
    text = text.strip()

    token = os.environ.get("TODOIST_API_TOKEN", "").strip().strip("\"'")
    if not token:
        sys.exit("Задайте змінну середовища TODOIST_API_TOKEN "
                 "(Todoist → Settings → Integrations → Developer).")

    try:
        labels = fetch_labels(token)
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status in (401, 403):
            sys.exit(f"Todoist відхилив токен (HTTP {status}). Перевірте TODOIST_API_TOKEN: "
                     f"це персональний токен із Settings → Integrations → Developer, "
                     f"без пробілів і лапок (довжина зараз: {len(token)}).")
        raise
    if not labels:
        sys.exit("У Todoist не знайдено жодної мітки.")

    if not args.no_fuzzy:
        keywords = get_clean_keywords(text, args.min_length)
        print(f"Ключові слова: {keywords}")
        print_table(fuzzy_search(labels, keywords, args.threshold)[: args.limit],
                    "Нечіткий пошук:", extra="query")

    if not args.no_semantic:
        try:
            rows = semantic_search(labels, text)
        except ImportError:
            print("\nСемантичний пошук пропущено: pip install 'todoist-labels[semantic]'")
        else:
            print_table(rows[: args.limit], "Семантичний пошук:")


if __name__ == "__main__":
    main()
