from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from minizinc import Instance, Model, Solver
from PIL import Image, ImageDraw, ImageFont

PRIMITIVE_DIST = 10
BOX_DIST = 10
BOX_TEXT_LEFT_PAD = 10
BOX_TEXT_TOP_PAD = 10
BOX_TEXT_RIGHT_EXTRA = 5
BOX_INNER_PAD = 10
BOX_MIN_TOP_PAD = 30
TEXT_FONT = "DejaVuSans.ttf"
FONT_CANDIDATES = (
    TEXT_FONT,
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
)


@dataclass(frozen=True)
class PackedPrimitive:
    members: tuple[str, ...]
    box_ids: tuple[int, ...]
    width: int
    height: int


@dataclass(frozen=True)
class ReducedInstance:
    box_names: list[str]
    box_enum: list[str]
    box_text_sizes: list[tuple[int, int]]
    primitives: list[PackedPrimitive]
    primitive_labels: list[str]
    primitive_enum: list[str]
    primitive_membership: list[list[bool]]
    require_primitive_containment: list[list[bool]]
    box_subset: list[list[bool]]
    box_nonoverlap_groups: list[list[int]]
    require_box_distance: list[list[bool]]
    coord_upper: int


@lru_cache(maxsize=None)
def resolve_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


@lru_cache(maxsize=None)
def measure_text(text: str, font_size: int) -> tuple[int, int]:
    font = resolve_font(font_size)
    image = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(image)
    text = text.replace("\\n", "\n")
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def text_size_with_margin(
    text: str, margin: tuple[int, int, int, int], font_size: int
) -> tuple[int, int]:
    width, height = measure_text(text, font_size)
    return (
        width + margin[0] + margin[1],
        height + margin[2] + margin[3],
    )


def pack_sizes(sizes: list[tuple[int, int]]) -> tuple[int, int]:
    if not sizes:
        return 0, 0

    root: dict[str, Any] = {
        "used": False,
        "pos": (0, 0),
        "size": [sizes[0][0], sizes[0][1]],
        "down": None,
        "right": None,
    }

    def find_node(
        node: dict[str, Any] | None, size: tuple[int, int]
    ) -> dict[str, Any] | None:
        if node is None:
            return None
        if node["used"]:
            return find_node(node["right"], size) or find_node(node["down"], size)
        if size[0] <= node["size"][0] and size[1] <= node["size"][1]:
            return node
        return None

    def split_node(node: dict[str, Any], size: tuple[int, int]) -> tuple[int, int]:
        node["used"] = True
        node["down"] = {
            "used": False,
            "pos": (node["pos"][0], node["pos"][1] + size[1]),
            "size": [node["size"][0], node["size"][1] - size[1]],
            "down": None,
            "right": None,
        }
        node["right"] = {
            "used": False,
            "pos": (node["pos"][0] + size[0], node["pos"][1]),
            "size": [node["size"][0] - size[0], size[1]],
            "down": None,
            "right": None,
        }
        return node["pos"]

    def grow_right(width: int, height: int) -> tuple[int, int] | None:
        nonlocal root
        original_root = {
            "used": root["used"],
            "pos": root["pos"],
            "size": list(root["size"]),
            "down": root["down"],
            "right": root["right"],
        }
        root = {
            "used": True,
            "pos": root["pos"],
            "size": [root["size"][0] + width, root["size"][1]],
            "right": {
                "used": False,
                "pos": (original_root["size"][0], 0),
                "size": [width, root["size"][1]],
                "down": None,
                "right": None,
            },
            "down": original_root,
        }
        node = find_node(root, (width, height))
        return split_node(node, (width, height)) if node is not None else None

    def grow_down(width: int, height: int) -> tuple[int, int] | None:
        nonlocal root
        original_root = {
            "used": root["used"],
            "pos": root["pos"],
            "size": list(root["size"]),
            "down": root["down"],
            "right": root["right"],
        }
        root = {
            "used": True,
            "pos": root["pos"],
            "size": [root["size"][0], root["size"][1] + height],
            "down": {
                "used": False,
                "pos": (0, original_root["size"][1]),
                "size": [root["size"][0], height],
                "down": None,
                "right": None,
            },
            "right": original_root,
        }
        node = find_node(root, (width, height))
        return split_node(node, (width, height)) if node is not None else None

    def grow_node(width: int, height: int) -> tuple[int, int] | None:
        can_grow_down = width <= root["size"][0]
        can_grow_right = height <= root["size"][1]
        should_grow_right = can_grow_right and (
            root["size"][1] >= root["size"][0] + width
        )
        should_grow_down = can_grow_down and (
            root["size"][0] >= root["size"][1] + height
        )
        if should_grow_right:
            return grow_right(width, height)
        if should_grow_down:
            return grow_down(width, height)
        if can_grow_right:
            return grow_right(width, height)
        if can_grow_down:
            return grow_down(width, height)
        return None

    max_x = 0
    max_y = 0
    for size in sizes:
        node = find_node(root, size)
        pos = split_node(node, size) if node is not None else grow_node(*size)
        if pos is None:
            raise RuntimeError("Packing failed for primitive text blocks")
        max_x = max(max_x, pos[0] + size[0])
        max_y = max(max_y, pos[1] + size[1])
    return max_x, max_y


def make_enum_values(values: list[str], prefix: str) -> list[str]:
    used: set[str] = set()
    enum_values: list[str] = []
    for index, value in enumerate(values, start=1):
        normalized = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if not normalized:
            normalized = f"{prefix}_{index}"
        if normalized[0].isdigit():
            normalized = f"{prefix}_{normalized}"
        candidate = normalized
        suffix = 2
        while candidate in used:
            candidate = f"{normalized}_{suffix}"
            suffix += 1
        used.add(candidate)
        enum_values.append(candidate)
    return enum_values


def maximal_cliques_from_adjacency(adjacency: list[set[int]]) -> list[list[int]]:
    cliques: list[list[int]] = []

    def bron_kerbosch(r: set[int], p: set[int], x: set[int]) -> None:
        if not p and not x:
            if len(r) >= 2:
                cliques.append(sorted(r))
            return

        pivot_candidates = p | x
        pivot = (
            max(pivot_candidates, key=lambda vertex: len(adjacency[vertex]))
            if pivot_candidates
            else None
        )
        pivot_neighbors = adjacency[pivot] if pivot is not None else set()
        for vertex in list(p - pivot_neighbors):
            bron_kerbosch(
                r | {vertex},
                p & adjacency[vertex],
                x & adjacency[vertex],
            )
            p.remove(vertex)
            x.add(vertex)

    bron_kerbosch(set(), set(range(len(adjacency))), set())
    cliques.sort(key=lambda clique: (len(clique), clique), reverse=True)
    return cliques


def reduce_csv(csv_path: Path) -> ReducedInstance:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.get_dialect("excel")
        rows = list(csv.reader(handle, dialect))
    header = rows[0]
    box_names = header[1:]
    box_enum = make_enum_values(box_names, "Box")
    primitive_names = [row[0] for row in rows[1:]]
    matrix = [tuple(value == "1" for value in row[1:]) for row in rows[1:]]

    grouped: dict[tuple[bool, ...], list[str]] = {}
    for primitive_name, membership in zip(primitive_names, matrix, strict=True):
        grouped.setdefault(membership, []).append(primitive_name)

    box_to_primitives: list[list[int]] = [[] for _ in box_names]
    primitives: list[PackedPrimitive] = []
    primitive_labels: list[str] = []
    primitive_membership: list[list[bool]] = []

    for membership in sorted(grouped):
        members = tuple(grouped[membership])
        box_ids = tuple(index + 1 for index, flag in enumerate(membership) if flag)
        element_sizes = sorted(
            [text_size_with_margin(member, (4, 4, 4, 4), 16) for member in members],
            key=lambda size: size[0],
            reverse=True,
        )
        packed_width, packed_height = pack_sizes(element_sizes)
        circle_cols = 1 if len(box_ids) == 1 else 2
        circle_rows = (len(box_ids) + circle_cols - 1) // circle_cols
        circle_width = (10 + 3 + 3) * circle_cols + 2 + 2
        circle_height = (10 + 3 + 3) * circle_rows + 2 + 2
        primitive = PackedPrimitive(
            members=members,
            box_ids=box_ids,
            width=packed_width + circle_width,
            height=max(packed_height, circle_height),
        )
        primitive_index = len(primitives)
        primitives.append(primitive)
        primitive_labels.append(" | ".join(members))
        primitive_membership.append(
            [box_index + 1 in box_ids for box_index in range(len(box_names))]
        )
        for box_index, flag in enumerate(membership):
            if flag:
                box_to_primitives[box_index].append(primitive_index)

    box_text_sizes = [
        text_size_with_margin(name, (0, 2, 0, 0), 18) for name in box_names
    ]
    box_sets = [set(indices) for indices in box_to_primitives]
    num_boxes = len(box_names)
    num_primitives = len(primitives)

    box_subset = [[False for _ in range(num_boxes)] for _ in range(num_boxes)]
    for outer in range(num_boxes):
        for inner in range(num_boxes):
            if outer == inner:
                continue
            if box_sets[inner] <= box_sets[outer]:
                box_subset[outer][inner] = True

    require_primitive_containment = [
        [primitive_membership[p][b] for p in range(num_primitives)]
        for b in range(num_boxes)
    ]
    for outer in range(num_boxes):
        for inner in range(num_boxes):
            if outer == inner or not box_subset[outer][inner]:
                continue
            for primitive_index in box_to_primitives[inner]:
                require_primitive_containment[outer][primitive_index] = False

    prevent_box_overlap = [[False for _ in range(num_boxes)] for _ in range(num_boxes)]
    require_box_distance = [[False for _ in range(num_boxes)] for _ in range(num_boxes)]
    for left in range(num_boxes):
        for right in range(left + 1, num_boxes):
            share_primitive = bool(box_sets[left] & box_sets[right])
            subset_relation = box_subset[left][right] or box_subset[right][left]
            if not share_primitive:
                prevent_box_overlap[left][right] = True
                prevent_box_overlap[right][left] = True
            elif not subset_relation:
                require_box_distance[left][right] = True
                require_box_distance[right][left] = True

    nonoverlap_adjacency = [
        {other for other in range(num_boxes) if prevent_box_overlap[box][other]}
        for box in range(num_boxes)
    ]
    nonoverlap_cliques = maximal_cliques_from_adjacency(nonoverlap_adjacency)
    box_nonoverlap_groups = nonoverlap_cliques

    total_max_size = sum(width for width, _ in box_text_sizes)
    total_max_size += sum(
        max(primitive.width, primitive.height) for primitive in primitives
    )
    coord_upper = max(1, 2 * total_max_size)
    primitive_enum = make_enum_values(primitive_labels, "Primitive")

    return ReducedInstance(
        box_names=box_names,
        box_enum=box_enum,
        box_text_sizes=box_text_sizes,
        primitives=primitives,
        primitive_labels=primitive_labels,
        primitive_enum=primitive_enum,
        primitive_membership=primitive_membership,
        require_primitive_containment=require_primitive_containment,
        box_subset=box_subset,
        box_nonoverlap_groups=box_nonoverlap_groups,
        require_box_distance=require_box_distance,
        coord_upper=coord_upper,
    )


def build_instance_data(reduced: ReducedInstance) -> dict[str, Any]:
    return {
        "Box": reduced.box_enum,
        "Primitive": reduced.primitive_enum,
        "coord_upper": reduced.coord_upper,
        "distance": {
            "primitive": PRIMITIVE_DIST,
            "box": BOX_DIST,
        },
        "padding": {
            "box_text_left": BOX_TEXT_LEFT_PAD,
            "box_text_top": BOX_TEXT_TOP_PAD,
            "box_text_right_extra": BOX_TEXT_RIGHT_EXTRA,
            "box_inner": BOX_INNER_PAD,
            "box_min_top": BOX_MIN_TOP_PAD,
        },
        "box_text_size": [
            {
                "width": size[0],
                "height": size[1],
            }
            for size in reduced.box_text_sizes
        ],
        "primitive_size": [
            {
                "width": primitive.width,
                "height": primitive.height,
            }
            for primitive in reduced.primitives
        ],
        "primitive_membership": reduced.primitive_membership,
        "require_primitive_containment": reduced.require_primitive_containment,
        "box_subset": reduced.box_subset,
        "box_nonoverlap_groups": [
            {reduced.box_enum[box] for box in group}
            for group in reduced.box_nonoverlap_groups
        ],
        "require_box_distance": reduced.require_box_distance,
    }


def export_instance_data(csv_path: Path) -> dict[str, Any]:
    reduced = reduce_csv(csv_path)
    data = build_instance_data(reduced)
    data["box_nonoverlap_groups"] = [
        {"set": sorted(group)} for group in data["box_nonoverlap_groups"]
    ]
    data["box_enum"] = reduced.box_enum
    data["primitive_enum"] = reduced.primitive_enum
    data["box_names"] = reduced.box_names
    data["primitive_labels"] = reduced.primitive_labels
    data["primitive_groups"] = [
        {
            "label": " | ".join(primitive.members),
            "members": list(primitive.members),
            "box_ids": list(primitive.box_ids),
            "width": primitive.width,
            "height": primitive.height,
        }
        for primitive in reduced.primitives
    ]
    return data


def solve_csv(
    csv_path: Path, solver_name: str = "gurobi", time_limit_seconds: int | None = None
) -> dict[str, Any]:
    reduced = reduce_csv(csv_path)
    model = Model(str(Path(__file__).with_name("recteuler.mzn")))
    solver = Solver.lookup(solver_name)
    instance = Instance(solver, model)
    for key, value in build_instance_data(reduced).items():
        instance[key] = value
    if time_limit_seconds is not None:
        result = instance.solve(timeout=timedelta(seconds=time_limit_seconds))
    else:
        result = instance.solve()

    runtime = result.statistics.get("time")
    runtime_seconds = (
        runtime.total_seconds() if isinstance(runtime, timedelta) else None
    )

    def rect_value(raw_rect: Any) -> dict[str, Any]:
        if isinstance(raw_rect, dict):
            x = raw_rect["x"]
            y = raw_rect["y"]
            width = raw_rect["width"]
            height = raw_rect["height"]
        elif hasattr(raw_rect, "x"):
            x = raw_rect.x
            y = raw_rect.y
            width = raw_rect.width
            height = raw_rect.height
        else:
            x, y, width, height = raw_rect
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

    def rects(raw_rects: list[Any], names: list[str]) -> list[dict[str, Any]]:
        return [
            {"name": name, **rect_value(raw_rect)}
            for name, raw_rect in zip(names, raw_rects, strict=True)
        ]

    response = {
        "status": str(result.status),
        "objective": result.objective,
        "runtime": runtime_seconds,
        "solution": None,
    }

    solution = result.solution
    if solution is None:
        return response

    response["solution"] = {
        "global_box": rect_value(solution.global_box),
        "z": solution.z,
        "boxes": rects(solution.boxes, reduced.box_names),
        "box_text_rects": rects(solution.box_text_rects, reduced.box_names),
        "primitives": rects(solution.primitives, reduced.primitive_labels),
    }
    return response


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="RectEuler MiniZinc utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser(
        "solve", help="Solve the RectEuler layout for a CSV input."
    )
    solve_parser.add_argument(
        "csv_path", type=Path, help="CSV file in the original RectEuler example format"
    )
    solve_parser.add_argument(
        "--solver", default="gurobi", help="MiniZinc solver id or name"
    )
    solve_parser.add_argument(
        "--time-limit-seconds", type=int, default=None, help="Optional solve time limit"
    )

    output_data_parser = subparsers.add_parser(
        "output-data",
        help="Write the generated MiniZinc instance data for a CSV input to JSON.",
    )
    output_data_parser.add_argument(
        "csv_path", type=Path, help="CSV file in the original RectEuler example format"
    )
    output_data_parser.add_argument(
        "output_json", type=Path, help="Where to write the generated JSON data"
    )

    args = parser.parse_args(argv)

    if args.command == "solve":
        result = solve_csv(
            args.csv_path,
            solver_name=args.solver,
            time_limit_seconds=args.time_limit_seconds,
        )
        print(json.dumps(result, indent=2))
        return

    if args.command == "output-data":
        data = export_instance_data(args.csv_path)
        args.output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
