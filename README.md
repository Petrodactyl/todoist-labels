# todoist-labels

Скрипт із Colab-ноутбука `Todoist-labels.ipynb`: шукає мітки Todoist, релевантні тексту
(нечіткий + семантичний пошук).

## Встановлення (раз)

    pipx install .                 # лише нечіткий пошук
    pipx install '.[semantic]'     # + семантичний (тягне torch, великий)

(або `pip install -e .`). Токен — у змінній середовища, напр. у `~/.bashrc`/`~/.zshrc`:

    export TODOIST_API_TOKEN=...

## Використання (з будь-якої теки)

    todoist-labels "Психологічне. Робота"
    todoist-labels -f opis.txt -n 10
    echo "текст" | todoist-labels --no-semantic
