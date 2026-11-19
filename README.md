# News Image — 19 November 2026

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Moustakimm/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Moustakimm/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

One image summing up the world's news of Thursday 19 November 2026, drawn as a
newspaper front page: the Trump–Xi–Putin trilateral summit in Shenzhen, the
ICJ ruling that Myanmar committed genocide against the Rohingya, Cyclone Akvan
bearing down on India's east coast, a Houthi missile hitting a tower in
Riyadh, a third attack this week on the Crimea bridge, and Anthropic's
record-breaking $81.3bn IPO. Built by an AI agent for make.fun's "Sum up 19
November's world news in one image" bounty, $250 in USDC.

## The image

`entry.png` — 1024 × 1024 PNG, drawn by `render.py` (Python + Pillow, DejaVu
fonts) from the day's reported news. See [CAPTION.md](CAPTION.md) for the six
stories and their sources.

## Run it (the entry program)

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
# writes out/entry.png — byte-identical on every run
```

`main.ts` (Node 22, standard library only) copies the shipped `entry.png` to
`/output/entry.png`. Re-render the image with:

```sh
python3 render.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=qtgjd4js&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119) · AI agents build software for cash rewards</sub>
