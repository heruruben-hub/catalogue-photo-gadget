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
