# VIDEO to MINECRAFT
Turn any `.mp4` or `.webm` into a datapack and resource that make that video play in minecraft blocks.

The script creates:
- a **datapack** that draws and animates the frames
- **resource pack** for playing the audio, will play on the same tick as the datapack starting
[![watch video](https://img.youtube.com/vi/pbrnvtbjSy4/0.jpg)](https://www.youtube.com/watch?v=pbrnvtbjSy4)

# VIDEO ^^^
## Requirements

- Python 3.10+
- 
-[FFmpeg](https://ffmpeg.org/) available with 'ffmpeg'

## Generate the packs

### Interactive (Recommended)

```bash
node tui.js
```
or the .bat/.sh files

Use arrow keys and enter to confirm. Will only take videos from this projects folder and its subfolders, will always output to `output` folder.

### Command Line (manual)
Use the following options when generating the Minecraft Java Edition datapack and resource pack:

| Argument | Type | Default | Description |
|---|---|---|---|
| `video` | `Path` | **Required** | Path to the input `.mp4` or `.webm` video. |
| `-o`, `--output` | `Path` | `output` | Directory where the generated datapack and resource pack will be saved. |
| `--size` | `WIDTHxHEIGHT` | `80x45` | Video resolution in blocks. Example: `160x90`. |
| `--origin` | `X Y Z` | `0 64 0` | Coordinates of the top-left block where the video screen spawns. |
| `--plane` | `xy`, `xz`, `zy` | `xy` | Orientation of the video screen. `xy` = vertical wall, `xz` = bird's-eye view, `zy` = side wall. |
| `--mode` | `mono`, `color` | `mono` | Video rendering mode. `mono` renders in monochrome; `color` renders in color. |
| `--foreground` | Block ID | `minecraft:white_concrete` | Block used for bright/foreground pixels. |
| `--background` | Block ID | `minecraft:air` | Block used for dark/background pixels. |
| `--threshold` | Byte value | `128` | Brightness threshold used when converting video frames to monochrome. |
| `--fps` | `float` | `20.0` | Video playback speed in frames per second. Valid range: `1–20`. Minecraft runs at 20 ticks per second. |
| `--pack-format` | `int` | `48` | Datapack format. `48` targets Minecraft Java Edition `1.21/1.21.1`. |
| `--resource-pack-format` | `int` | `34` | Resource pack format. `34` targets Minecraft Java Edition `1.21/1.21.1`. |
| `--legacy-folders` | Flag | Disabled | Uses the legacy `functions/` and `tags/functions/` folder structure for Minecraft `1.20.4` and older. |

### Example

The shortest command is:

```bash
python generate.py my-video.mp4
```

WebM works the same way:

```bash
python generate.py my-video.webm
```

Useful examples:

```bash
# Colour, 96 by 54 blocks, top-left at X=100 Y=120 Z=-30
python generate.py my-video.mp4 --mode color --size 96x54 --origin 100 120 -30

# Use one block for white pixels and empty space for black pixels
python generate.py my-video.mp4 --size 64x36 --foreground diamond_block

# Or choose blocks for both white and black pixels
python generate.py my-video.mp4 --size 64x36 --foreground quartz_block --background black_concrete

# Put the screen flat on the ground, extending toward +X and +Z
python generate.py my-video.mp4 --mode color --plane xz --origin 0 64 0
```

Run `python generate.py --help` for every option. Existing output is never removed unless you pass `--overwrite`.

### Coordinates and direction

`--origin X Y Z` is the top-left pixel. The plane controls where pixels continue:

| Plane | Width goes toward | Height goes toward |
|---|---|---|
| `xy` | +X | -Y |
| `xz` | +X | +Z |
| `zy` | +Z | -Y |


## Install and play

1. Copy `output/datapack.zip` into your world's `datapacks` directory.
2. Copy `output/resourcepack.zip` into your Minecraft `resourcepacks` directory and enable it.
3. Enter/reload the world, stand somewhere with the screen's chunks loaded, and run:

```mcfunction
/function blockvideo:play
```

Stop both animation and audio with:

```mcfunction
/function blockvideo:stop
```

The sound is played on the `master` channel with no distance fade, so every current player with the resource pack hears it. Players joining after playback begins will not join the audio midway through.

## Version compatibility

The defaults, data pack format `48`, resource pack format `34`, and singular `function` folders—target Java 1.21/1.21.1. For another release, pass its formats with `--pack-format` and `--resource-pack-format`. Minecraft 1.20.4 and older also needs `--legacy-folders`.
