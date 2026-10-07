"""Пошук релевантних міток Todoist за текстом контексту.

Два види пошуку (як у оригінальному Colab-ноутбуці):
  * нечіткий (thefuzz, partial_ratio) по очищених ключових словах;
  * семантичний (sentence-transformers) по повному тексту — опційно.
"""
import argparse
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
    from thefuzz import fuzz

    best = {}
    for q in queries:
        for label in labels:
            score = fuzz.partial_ratio(q, label["name"])
            if score >= threshold and score > best.get(label["id"], (None, -1))[1]:
                best[label["id"]] = (q, score, label)
    rows = [{**lab, "query": q, "score": s} for q, s, lab in best.values()]
    return sorted(rows, key=lambda r: r["score"], reverse=True)


def semantic_search(labels, text):
    from sentence_transformers import SentenceTransformer, util

    model = SentenceTransformer(SEMANTIC_MODEL)
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
    args = p.parse_args(argv)

    if args.file:
        text = open(args.file, encoding="utf-8").read()
    elif args.text:
        text = " ".join(args.text)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        p.error("потрібен текст контексту (аргумент, --file або stdin)")
    text = text.strip()

    token = os.environ.get("TODOIST_API_TOKEN")
    if not token:
        sys.exit("Задайте змінну середовища TODOIST_API_TOKEN "
                 "(Todoist → Settings → Integrations → Developer).")

    labels = fetch_labels(token)
    if not labels:
        sys.exit("У Todoist не знайдено жодної мітки.")

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
