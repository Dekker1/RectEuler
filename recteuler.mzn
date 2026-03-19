% RectEuler MiniZinc extraction from the original worker-side Gurobi model.

enum Box;
enum Primitive;

int: coord_upper;

type Size = record(
	int: width,
	int: height,
);

type PaddingConfig = record(
	int: box_text_left,
	int: box_text_top,
	int: box_text_right_extra,
	int: box_inner,
	int: box_min_top,
);

type DistanceConfig = record(
	int: primitive,
	int: box,
);

type Margins = record(
	int: left,
	int: top,
	int: right,
	int: bottom,
);

PaddingConfig: padding;
DistanceConfig: distance;

array[Box] of Size: box_text_size;
array[Primitive] of Size: primitive_size;
array[Primitive, Box] of bool: primitive_membership;
array[Box, Primitive] of bool: require_primitive_containment;
array[Box, Box] of bool: box_subset;
array[Box, Box] of bool: prevent_box_overlap;
array[Box, Box] of bool: require_box_distance;

% Decision variables recreated from:
% - /Users/dekker1/Code/temp/RectEuler/docker-files/worker/code/Box_gurobi.py:14-25
% - /Users/dekker1/Code/temp/RectEuler/docker-files/worker/code/ElementGroup_gurobi.py:13-17
% - /Users/dekker1/Code/temp/RectEuler/docker-files/worker/code/main.py:165-173
type Rect = record(
	var 0..coord_upper: x,
	var 0..coord_upper: y,
	var 0..coord_upper: width,
	var 0..coord_upper: height,
);

% Shared containment relation for axis-aligned rectangles with explicit margins.
% This is used for primitive containment, subset-box containment, and coverage by
% the global bounding box.
predicate rect_contains(
	Rect: outer,
	Rect: inner,
	Margins: margins,
) =
	inner.x - outer.x >= margins.left
	/\ inner.y - outer.y >= margins.top
	/\ (outer.x + outer.width) - (inner.x + inner.width) >= margins.right
	/\ (outer.y + outer.height) - (inner.y + inner.height) >= margins.bottom;

predicate rect_contains(Rect: outer, Rect: inner) =
	rect_contains(outer, inner, (left: 0, top: 0, right: 0, bottom: 0));

Rect: global_box ::output = let {
	var 0..coord_upper: width;
	var 0..coord_upper: height;
} in (x: 0, y: 0, width: width, height: height);
array[Box] of Rect: boxes;
array[Box] of Rect: box_text_rects ::output = [
	let {
		var 0..coord_upper: x;
		var 0..coord_upper: y;
	} in (x: x, y: y, width: box_text_size[b].width, height: box_text_size[b].height)
	| b in Box
];
array[Primitive] of Rect: primitives ::output = [
	let {
		var 0..coord_upper: x;
		var 0..coord_upper: y;
	} in (x: x, y: y, width: primitive_size[p].width, height: primitive_size[p].height)
	| p in Primitive
];

% Original "squareness" helper reproduced from /docker-files/worker/code/main.py:173-176.
% Note: the original formulation uses |globalBox.x2 - globalBox.y2| rather than
% |(globalBox.x2 - globalBox.x1) - (globalBox.y2 - globalBox.y1)|. This model
% keeps the exact value because global_box.x and global_box.y are fixed to 0.
var 0..coord_upper: z ::output = abs(global_box.width - global_box.height);

% Box label geometry from /docker-files/worker/code/Box_gurobi.py:29-35.
% These constraints place the set name inside each box and ensure the box is
% wide enough for its label.
constraint forall(b in Box) (
	box_text_rects[b].x = boxes[b].x + padding.box_text_left
	/\ box_text_rects[b].y = boxes[b].y + padding.box_text_top
	/\ boxes[b].width >= box_text_rects[b].width + padding.box_text_right_extra
);

% Primitive containment inside its boxes from /docker-files/worker/code/Box_gurobi.py:37-43.
% The Python data builder reproduces the later removePrimitiveConstrains() calls
% triggered by subset boxes in /docker-files/worker/code/ModelConstraints.py:42-60.
constraint forall(b in Box, p in Primitive where require_primitive_containment[b, p]) (
	rect_contains(
		boxes[b],
		primitives[p],
		(
			left: padding.box_inner,
			top: max(padding.box_min_top, box_text_size[b].height + padding.box_inner),
			right: padding.box_inner,
			bottom: padding.box_inner,
		),
	)
);

% Global bounding-box coverage from /docker-files/worker/code/main.py:202-206.
constraint forall(b in Box) (
	rect_contains(
		global_box,
		boxes[b],
	)
);

% Box-subset constraints from /docker-files/worker/code/ModelConstraints.py:41-59.
% If box_subset[outer, inner] is true, then inner must sit strictly inside outer.
constraint forall(outer, inner in Box where outer != inner /\ box_subset[outer, inner]) (
	rect_contains(
		boxes[outer],
		boxes[inner],
		(
			left: distance.box,
			top: distance.box + box_text_size[outer].height,
			right: distance.box,
			bottom: distance.box,
		),
	)
);

% Primitive exclusion from non-member boxes, recreated from
% /docker-files/worker/code/ModelConstraints.py:13-27.
% Original Gurobi version used four binaries and big-M:
%   b1 + b2 + b3 + b4 <= 3
%   primitive.x2 + primitiveDist <= box.x1 + M*b1
%   primitive.y2 + primitiveDist <= box.y1 + M*b2
%   box.x2 + primitiveDist <= primitive.x1 + M*b3
%   box.y2 + primitiveDist <= primitive.y1 + M*b4
% MiniZinc version uses the native disjunction directly.
constraint forall(p in Primitive, b in Box where not primitive_membership[p, b]) (
	primitives[p].x + primitives[p].width + distance.primitive <= boxes[b].x
	\/ primitives[p].y + primitives[p].height + distance.primitive <= boxes[b].y
	\/ boxes[b].x + boxes[b].width + distance.primitive <= primitives[p].x
	\/ boxes[b].y + boxes[b].height + distance.primitive <= primitives[p].y
);

% Set-name non-overlap from /docker-files/worker/code/ModelConstraints.py:63-82.
% Original formulation again used four binaries plus big-M; this keeps the same
% four-way separation as a direct logical disjunction.
constraint forall(b1, b2 in Box where b1 < b2) (
	box_text_rects[b1].x + box_text_rects[b1].width + distance.primitive <= box_text_rects[b2].x
	\/ box_text_rects[b1].y + box_text_rects[b1].height + distance.primitive <= box_text_rects[b2].y
	\/ box_text_rects[b2].x + box_text_rects[b2].width + distance.primitive <= box_text_rects[b1].x
	\/ box_text_rects[b2].y + box_text_rects[b2].height + distance.primitive <= box_text_rects[b1].y
);

% Non-overlap for disjoint boxes from /docker-files/worker/code/ModelConstraints.py:84-107.
% The original used the same four-binary big-M pattern; MiniZinc uses a direct
% disjunction of the four relative placements.
constraint forall(b1, b2 in Box where b1 < b2 /\ prevent_box_overlap[b1, b2]) (
	boxes[b1].x + boxes[b1].width + distance.primitive <= boxes[b2].x
	\/ boxes[b1].y + boxes[b1].height + distance.primitive <= boxes[b2].y
	\/ boxes[b2].x + boxes[b2].width + distance.primitive <= boxes[b1].x
	\/ boxes[b2].y + boxes[b2].height + distance.primitive <= boxes[b1].y
);

% Edge-distance constraints for overlapping, non-nested boxes from
% /docker-files/worker/code/ModelConstraints.py:109-160.
% Original Gurobi formulation linearised each absolute value with a dedicated
% binary and big-M pair of inequalities. MiniZinc can state the intended form
% directly as abs(edge_a - edge_b) >= box_dist.
constraint forall(b1, b2 in Box where b1 < b2 /\ require_box_distance[b1, b2]) (
	abs((boxes[b1].x + boxes[b1].width) - boxes[b2].x) >= distance.box
	/\ abs(boxes[b1].x - boxes[b2].x) >= distance.box
	/\ abs((boxes[b1].x + boxes[b1].width) - (boxes[b2].x + boxes[b2].width)) >= distance.box
	/\ abs((boxes[b2].x + boxes[b2].width) - boxes[b1].x) >= distance.box
	/\ abs((boxes[b1].y + boxes[b1].height) - boxes[b2].y) >= distance.box
	/\ abs(boxes[b1].y - boxes[b2].y) >= distance.box
	/\ abs((boxes[b1].y + boxes[b1].height) - (boxes[b2].y + boxes[b2].height)) >= distance.box
	/\ abs((boxes[b2].y + boxes[b2].height) - boxes[b1].y) >= distance.box
);

% Objective from /docker-files/worker/code/main.py:214-216.
% This minimizes box perimeters-ish extents plus the enclosing box size and z.
solve minimize
	sum(b in Box)(boxes[b].width + boxes[b].height)
	+ global_box.width
	+ global_box.height
	+ z;
