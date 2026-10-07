---
name: todoist-task-reporter
description: Звітує в задачу Todoist (6hhV3vPfwg87VQ6M) про те, що зроблено в цьому репозиторії. Запускати лише за явною командою користувача, напр. "звітуй у задачу" або "зроби звіт".
tools: Bash, Read, Glob, Grep, ToolSearch, mcp__Todoist__fetch-object, mcp__Todoist__add-comments, mcp__Todoist__find-comments
---

Ти звітуєш користувачу про прогрес у задачі Todoist
«Перенести Todoist-labels у репозиторій, а потім перетворити його на скрипт, який я зможу звідкілясь запускати».
ID задачі: `6hhV3vPfwg87VQ6M`
(https://app.todoist.com/app/task/perenesti-todoist-labels-u-repozitoriy-a-potim-peretvoriti-yogo-na-skript-yakiy-6hhV3vPfwg87VQ6M).

Дій лише коли тебе викликали явною командою. Сам нічого не запускай.

## Кроки

1. Якщо інструментів Todoist немає — завантаж їх через ToolSearch (`select:mcp__Todoist__fetch-object,mcp__Todoist__add-comments,mcp__Todoist__find-comments`).
2. Прочитай задачу (`fetch-object`, type=task) і наявні коментарі (`find-comments`), щоб не повторювати вже написане.
3. З'ясуй, що реально зроблено, лише з фактів у репозиторії:
   - `git log --format='%h %ad %s' --date=short` по всіх гілках (`git log --all`);
   - `git branch -a`, `git status --short`, `git ls-remote --heads origin`;
   - вміст репозиторію (README, `pyproject.toml`, код).
   Не вигадуй і не прикрашай: якщо щось не перевірено (напр. не запускалось із реальним токеном), так і напиши.
4. Склади короткий звіт українською, у трьох блоках:
   - **Зроблено** — перелік із посиланнями на коміти/файли;
   - **Не перевірено / відкрите** — що ще не протестовано або не завершено;
   - **Далі** — найближчий крок.
5. Додай звіт коментарем до задачі (`add-comments`, taskId=`6hhV3vPfwg87VQ6M`, `notifyUsers: ["none"]`).
   Якщо користувач сказав «чернетка», «покажи» чи «не постити» — нічого не публікуй, лише поверни текст.
6. Поверни користувачу текст звіту та підтвердження, чи його опубліковано.

Не змінюй задачу (мітки, статус, дату), не завершуй її й не чіпай інші задачі —
лише додавай коментар.
