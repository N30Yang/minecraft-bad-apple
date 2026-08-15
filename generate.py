#!/usr/bin/env python3
"""Turn an MP4 or WebM video into a Minecraft video pack."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

NAMESPACE = "blockvideo"

COLOR_PALETTE = {
    "minecraft:black_concrete": (8, 10, 15),
    "minecraft:gray_concrete": (55, 58, 62),
    "minecraft:light_gray_concrete": (125, 125, 115),
    "minecraft:white_concrete": (207, 213, 214),
    "minecraft:brown_concrete": (96, 60, 32),
    "minecraft:red_concrete": (142, 33, 33),
    "minecraft:orange_concrete": (224, 97, 0),
    "minecraft:yellow_concrete": (241, 175, 21),
    "minecraft:lime_concrete": (94, 169, 24),
    "minecraft:green_concrete": (73, 91, 36),
    "minecraft:cyan_concrete": (21, 119, 136),
    "minecraft:light_blue_concrete": (36, 137, 199),
    "minecraft:blue_concrete": (44, 46, 143),
    "minecraft:purple_concrete": (100, 31, 156),
    "minecraft:magenta_concrete": (169, 48, 159),
    "minecraft:pink_concrete": (214, 101, 143),
    "minecraft:black_wool": (20, 21, 25),
    "minecraft:gray_wool": (62, 68, 71),
    "minecraft:light_gray_wool": (142, 142, 135),
    "minecraft:white_wool": (234, 236, 237),
    "minecraft:brown_wool": (114, 71, 40),
    "minecraft:red_wool": (161, 39, 35),
    "minecraft:orange_wool": (240, 118, 19),
    "minecraft:yellow_wool": (249, 198, 39),
    "minecraft:lime_wool": (112, 185, 25),
    "minecraft:green_wool": (84, 109, 27),
    "minecraft:cyan_wool": (21, 137, 145),
    "minecraft:light_blue_wool": (58, 175, 217),
    "minecraft:blue_wool": (53, 57, 157),
    "minecraft:purple_wool": (121, 42, 172),
    "minecraft:magenta_wool": (189, 68, 179),
    "minecraft:pink_wool": (237, 141, 172),
    "minecraft:black_terracotta": (37, 22, 16),
    "minecraft:gray_terracotta": (57, 42, 35),
    "minecraft:light_gray_terracotta": (135, 106, 97),
    "minecraft:white_terracotta": (210, 178, 161),
    "minecraft:brown_terracotta": (77, 51, 36),
    "minecraft:red_terracotta": (143, 61, 47),
    "minecraft:orange_terracotta": (161, 83, 37),
    "minecraft:yellow_terracotta": (186, 133, 35),
    "minecraft:lime_terracotta": (103, 117, 52),
    "minecraft:green_terracotta": (76, 83, 42),
    "minecraft:cyan_terracotta": (87, 91, 91),
    "minecraft:light_blue_terracotta": (113, 108, 137),
    "minecraft:blue_terracotta": (74, 59, 91),
    "minecraft:purple_terracotta": (118, 70, 86),
    "minecraft:magenta_terracotta": (150, 88, 109),
    "minecraft:pink_terracotta": (162, 78, 79),
    "minecraft:snow_block": (239, 251, 251),
    "minecraft:quartz_block": (235, 229, 222),
    "minecraft:smooth_sandstone": (219, 207, 163),
    "minecraft:end_stone": (219, 224, 158),
    "minecraft:sandstone": (216, 203, 155),
    "minecraft:oak_planks": (162, 130, 79),
    "minecraft:spruce_planks": (114, 84, 48),
    "minecraft:acacia_planks": (168, 90, 50),
    "minecraft:cherry_planks": (226, 178, 172),
    "minecraft:mangrove_planks": (117, 54, 48),
    "minecraft:warped_planks": (43, 104, 99),
    "minecraft:crimson_planks": (101, 48, 70),
    "minecraft:stone": (125, 125, 125),
    "minecraft:cobblestone": (127, 127, 127),
    "minecraft:deepslate": (76, 76, 80),
    "minecraft:tuff": (108, 109, 102),
    "minecraft:mud": (60, 57, 60),
    "minecraft:netherrack": (111, 54, 52),
    "minecraft:nether_bricks": (44, 21, 26),
    "minecraft:prismarine": (99, 156, 151),
    "minecraft:dark_prismarine": (51, 91, 75),
    "minecraft:purpur_block": (169, 125, 169),
    "minecraft:lapis_block": (30, 67, 140),
    "minecraft:diamond_block": (98, 237, 228),
    "minecraft:emerald_block": (42, 203, 87),
    "minecraft:gold_block": (246, 208, 61),
    "minecraft:raw_iron_block": (166, 135, 107),
    "minecraft:raw_copper_block": (154, 105, 79),
    "minecraft:oxidized_copper": (82, 162, 132),
}


def block_id(value: str) -> str:
    if not re.fullmatch(r"(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+(?:\[[^\]]+\])?", value):
        raise argparse.ArgumentTypeError(f"invalid block state")
    return value if ":" in value else "minecraft:" + value


def size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)[xX](\d+)", value)
    if not match or min(map(int, match.groups())) < 1:
        raise argparse.ArgumentTypeError("size must look like 80:45")
    return int(match.group(1)), int(match.group(2))


def byte_value(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a whole number form 0 to 255")
    if not 0 <= number <= 255:
        raise argparse.ArgumentTypeError("must be from 0 to 255")
    return number


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a java edition datapack and resource pack to display a mp4 or webm",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("video", type=Path, help="any .mp4 or .webm video")
    p.add_argument("-o", "--output", type=Path, default=Path("output"))
    p.add_argument(
        "--size", type=size, default=(80, 45), metavar="WIDTHxHEIGHT eg 160x90"
    )
    p.add_argument(
        "--origin",
        nargs=3,
        type=int,
        default=(0, 64, 0),
        metavar=("X", "Y", "Z"),
        help="top-left block of the screen, where the video spawns",
    )
    p.add_argument(
        "--plane",
        choices=("xy", "xz", "zy"),
        default="xy",
        help="screen axes; xy is a vertical wall, xz is birds eye view, zy is a side wall",
    )
    p.add_argument("--mode", choices=("mono", "color"), default="mono")
    p.add_argument("--foreground", type=block_id, default="minecraft:white_concrete")
    p.add_argument(
        "--background",
        type=block_id,
        default="minecraft:air",
        help="dark pixel block; defaults to air",
    )
    p.add_argument("--threshold", type=byte_value, default=128)
    p.add_argument(
        "--fps",
        type=float,
        default=20.0,
        help="1-20; Minecraft runs at 20 ticks per second",
    )
    p.add_argument(
        "--pack-format",
        type=int,
        default=48,
        help="data pack format (48 is java 1.21/1.21.1)",
    )
    p.add_argument(
        "--resource-pack-format",
        type=int,
        default=34,
        help="resource pack format, 34 targets 1.21/1.21.1)",
    )
    p.add_argument(
        "--legacy-folders",
        action="store_true",
        help="use functions/tags/functions for minecraft 1.20.4 and older",
    )
    p.add_argument("--overwrite", action="store_true")
    return p


def write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def make_zip(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(source.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(source))


def coords(
    origin: tuple[int, int, int], plane: str, x: int, y: int
) -> tuple[int, int, int]:
    ox, oy, oz = origin
    if plane == "xy":
        return ox + x, oy - y, oz
    if plane == "xz":
        return ox + x, oy, oz + y
    return ox, oy - y, oz + x

def nearest_block(bgr, palette_items) -> str:
    b, g, r = map(int, bgr)
    return min(palette_items, key=lambda item:
               2 * (r - item[1][0]) ** 2 + 4 * (g - item[1][1]) ** 2 + 3 * (b - item[1][2]) ** 2)[0]

def extract_audio(video: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
                "-vn", "-c:a", "libvorbis", "-q:a", "5", str(destination)]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        raise SystemExit("FFMpeg is required for audio. Install it and run again.")
    except subprocess.CalledProcessError:
        raise SystemExit("FFMpeg could not etract audio from this video.")

def probe_video(video: Path) -> tuple[str, int, int, float]:
    command = ["ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height,avg_frame_rate",
                "-of", "json", str(video)]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        stream = json.loads(result.stdout)["streams"][0]
        fps = float(Fraction(stream["avg_frame_rate"])), int(stream["height"]), fps
        return stream["codec_name"], int(stream["width"]), int(stream["height"]), fps
    except FileNotFoundError:
        raise SystemExit("FFMpeg and FFprobe are required. install and try again.")
    except (subprocess.CalledProcessError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        raise SystemExit("FFprobe could not read the video stream.")

def ffmpeg_frames(video: Path, width: int, height: int, codec: str):
    command = ["ffmpeg", "-hide-banner", "-loglevel", "error"]
    if codec == "av1":
        command += ["-c:v", "libdav1d"]
    command += ["-i", str(video), "-map", "0:v:0", "-an",
                "-vf", f"scale={width}:{height}:flags=area",
                "-pix_fmt", "bgr24", "-f", "rawvideo", "pipe:1"]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
    except FileNotFoundError:
        raise SystemExit("FFmpeg is required. install it and try again.")

    frame_bytes = width * height * 3
    assert process.stdout is not None
    try:
        while True:
            data = process.stdout.read(frame_bytes)
            if not data:
                break
            while len(data) < frame_bytes:
                chunk = process.stdout.read(frame_bytes - len(data))
                if not chunk:
                    break
                data += chunk
            if len(data) != frame_bytes:
                break
            yield data
    finally:
        process.stdout.close()
        return_code = process.wait()
    if return_code != 0:
        raise SystemExit("FFmpeg could not decode the video frames.")
    
def main() -> None:
    args = parser().parse.args()
    if not args.video.is_file():
        raise SystemExit(f"video not found: {args.video}")
    if args.video.suffix.lower() not in {".mp4", ".webm"}:
        raise SystemExit("input must be an .mp4 or .webm")
    if not (1 <= args.fps <= 20):
        raise SystemExit("--fps must be between 1 and 20")
    if args.output.exists():
        if not args.overwrite:
            raise SystemExit(f"Ouput exists: {args.output} (pass --overwrite to replace it)")
        shutil.rmtree(args.output)
    
    datapack = args.output / "datapack"
    resourcepack = args.output/"resourcepack"
    has_audio = True
    function_dir = "functions" if args.legacy_folders else "function"
    tag_dir = "functions" if args.legacy_folders else "function"
    functions = datapack / "data" / NAMESPACE / function_dir

    datapack_meta = {"pack": {"pack_format": args.pack_format, "description": "Video made with block video"}}
    write(datapack/"pack.mcmeta",json.dumps(datapack_meta, indent=2))
    if has_audio:
        resourcepack_meta = {"pack": {"pack_format": args.pack_format, "description": "Video made with Block Video"}}
        write(resourcepack / "pack.mcmeta", json.dumps(resourcepack_meta, indent=2))
    write(datapack / "data/minecraft/tags" / tag_dir / "load.json",
          json.dumps({"values": [f"{NAMESPACE}:load"]}, indent=2))
    write(datapack / "data/minecraft/tags" / tag_dir / "tick.json",
          json.dumps({"values": [f"{NAMESPACE}:tick"]}, indent=2))
    
    if has_audio:
        sounds = {"video": {"sounds": [{"name": f"{NAMESPACE}:video", "stream": True}]}}
        write(resourcepack / "assets" / NAMESPACE / "sounds.json", json.dumps(sounds, indent=2))
        extract_audio(args.video, resourcepack / "assets" / NAMESPACE / "sounds/video.ogg")
    
    codec, _, _, source_fps = probe_video(args.video)
    if not math.isfinite(source_fps) or source_fps <= 0:
        source_fps=args.fps
    render_fps = min(args.fps, source_fps)
    if render_fps < args.fps:
        print(f"source is only {source_fps:g} fps; using {render_fps:g} fps to keep duration the same")
    width, height = args.size
    frame_stream = ffmpeg_frames(args.video, width, height, codec)
    palette_items = list(COLOR_PALETTE.items())
    previous = [None] * (width*height)
    output_index = 0
    commands_total = 0
    next_output_time = 0.0
    output_times = []
    media_end_time = 0.0
    

    print(f"generating {width}x{height} at {render_fps:g} fps ({args.mode})...")
    for source_index, frame in enumerate(frame_stream):
        source_time = source_index / source_fps
        frame_end_time = source_time + 1/ source_fps
        media_end_time = frame_end_time
        if source_time + 1e-9 < next_output_time:
            continue
        next_output_time = (output_index +1) / render_fps
        frame_commands = []
        for py in range(height):
            for px in range(width):
                offset = (py*width+px)*3
                pixel = frame[offset:offset +3]
                if args.mode == "mono":
                    luminance = int(pixel[2] * .2126 + pixel[1]*.7152+pixel[0]*.0722)
                    block = args.foreground if luminance >= args.threshold else args.background
                else:
                    block = nearest_block(pixel, palette_items)
                pos = py*width + px
                if previous[pos] == block:
                    continue
                previous[pos] = block
                bx, by, bz = coords(tuple(args.origin), args.plane, px, py)
                frame_commands.append(f"setblock {bx} {by} {bz} {block}\n")
        write(functions / "frames" /f"f{output_index}.mcfunction", "".join(frame_commands))
        commands_total += len(frame_commands)
        output_times.appened(source_time)
        output_index += 1
        if output_index % 100 == 0:
            print(f"  {output_index} frames", flush=True)
    if output_index == 0:
        raise SystemExit("The video contained no readable frames.")

    tick_lines = [f"execute if score #playing {NAMESPACE} matches 1 run scoreboard players add #frame {NAMESPACE} 1\n"]
    for index, output_time in enumerate(output_times):
        game_tick = round(output_time * 20)
        tick_lines.append(
            f"execute if score #playing {NAMESPACE} matches 1 if score #frame {NAMESPACE} matches {game_tick} run function {NAMESPACE}:frames/f{index}\n"
        )
    final_tick = math.ceil(media_end_time * 20)
    tick_lines.append(f"execute if score #frame {NAMESPACE} matches {final_tick}.. run scoreboard players set #playing {NAMESPACE} 0\n")
    write(functions / "tick.mcfunction", "".join(tick_lines))
    write(functions / "load.mcfunction",
          f"scoreboard objectives add {NAMESPACE} dummy\nscoreboard players set #playing {NAMESPACE} 0\n")
    ox, oy, oz = args.origin
    play_lines =[]
    if has_audio:
        play_lines.append(f"stopsound @a master {NAMESPACE}:video\n")
    play_lines.extend((f"scoreboard players set #frame {NAMESPACE} -1\n",
                       f"scoreboard players set #playing {NAMESPACE} 1\n"))
    if has_audio:
        play_lines.append(f"playsound {NAMESPACE}:video master @a {ox} {oy} {oz} 1 1 1\n")
    write(functions / "play.mcfunction", "".join(play_lines))
    stop = f"scoreboard players set #playing {NAMESPACE} 0\n"
    if has_audio:
        stop += f"stopsound @a master {NAMESPACE}:video\n"
    write(functions / "stop.mcfunction", stop)

    details = {
        "video": str(args.video), "frames": output_index, "fps": render_fps,
        "resolution": [width, height], "origin": args.origin, "plane": args.plane,
        "mode": args.mode, "block_changes": commands_total, "audio": has_audio,
    }
    write(args.output / "generation.json", json.dumps(details, indent=2))
    make_zip(datapack, args.output / "datapack.zip")
    if has_audio:
        make_zip(resourcepack, args.output / "resourcepack.zip")
    print(f"Done: {output_index} frames, {commands_total:,} block changes")
    print(f"Datapack:      {args.output / 'datapack.zip'}")
    if has_audio:
        print(f"Resource pack: {args.output / 'resourcepack.zip'}")
    print(f"In Minecraft run: /function {NAMESPACE}:play")


if __name__ == "__main__":
    main()
        