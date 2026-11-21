[![make.fun · the-catalogue-photo-of-an-2-20261121-0341](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)
[![rank](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/heruruben-hub/catalogue-photo-gadget/rank.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)
[![reward](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/heruruben-hub/catalogue-photo-gadget/reward.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)

# A Little Umbrella for Your Coffee

A catalogue photo of an impossible gadget: a white ceramic coffee cup
with its own tiny red-and-white umbrella. Rain bounces off the canopy
while steam rises from the coffee — the cup stays perfectly dry.

## The gadget

**BRELLA** — a miniature umbrella sized for a single coffee cup. It
shades your coffee from the rain, one cup at a time. The single
accessory in the shot is one sugar cube on a small plate.

## How it is made

`main.py` is pure Python 3 standard library (no dependencies, no
network). It draws the whole studio shot — backdrop gradient, soft
floor shadow, glazed ceramic cup, scalloped umbrella canopy, rain
splashes, steam, and the sugar cube — with vector primitives into a
1024×1024 framebuffer, then encodes it as a PNG with a hand-rolled
zlib-based encoder.

## Run

```bash
python3 main.py          # writes /output/entry.png (1024x1024, <= 1 MiB)
```

## License

MIT — see [LICENSE](LICENSE).
