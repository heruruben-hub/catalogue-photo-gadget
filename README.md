# A Little Umbrella for Your Coffee

make.fun entry for **The Catalogue Photo of an Impossible Gadget**
(`the-catalogue-photo-of-an-2-20261121-0341`).

## The gadget

A white ceramic coffee cup that keeps itself dry with its own tiny
umbrella. Rain bounces off the little red-and-white canopy while steam
curls up from the coffee beneath it. A single sugar cube sits beside
the cup as the one accessory. The joke reads at a glance: an umbrella
for a cup of coffee.

## How it works

`main.py` (Python 3.13 standard library only, no network) draws the
studio catalogue photograph from scratch — a scanline rasterizer with
a hand-rolled PNG encoder (zlib + struct) — and writes
`/output/entry.png`, a 1024×1024 PNG.

```sh
python3 main.py        # writes $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png)
```

## License

MIT — see `LICENSE`.
