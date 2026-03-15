% RectEuler MiniZinc extraction from the original worker-side Gurobi model.

enum Box;
enum Primitive;

float: coord_upper;

type Size = record(
	float: width,
	float: height,
);

type PaddingConfig = record(
	float: box_text_left,
	float: box_text_top,
	float: box_text_right_extra,
	float: box_inner,
	float: box_min_top,
);

type DistanceConfig = record(
	float: primitive,
	float: box,
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
	var 0.0..coord_upper: x1,
	var 0.0..coord_upper: y1,
	var 0.0..coord_upper: x2,
	var 0.0..coord_upper: y2,
);

Rect: global_box;
array[Box] of Rect: boxes;
array[Box] of Rect: box_text_rects;
array[Primitive] of Rect: primitives;
var 0.0..coord_upper: z;

% Global bounding box anchor from /docker-files/worker/code/main.py:170-171.
constraint global_box.x1 = 0.0;
constraint global_box.y1 = 0.0;

% Original "squareness" helper reproduced from /docker-files/worker/code/main.py:173-176.
% Note: the original formulation uses |globalBox.x2 - globalBox.y2| rather than
% |(globalBox.x2 - globalBox.x1) - (globalBox.y2 - globalBox.y1)|. This model
% keeps that exact formulation.
constraint global_box.x2 - global_box.y2 <= z;
constraint -(global_box.x2 - global_box.y2) <= z;

% Box label geometry from /docker-files/worker/code/Box_gurobi.py:29-35.
% These constraints place the set name inside each box and ensure the box is
% wide enough for its label.
constraint forall(b in Box) (
	box_text_rects[b].x1 = boxes[b].x1 + padding.box_text_left
	/\ box_text_rects[b].y1 = boxes[b].y1 + padding.box_text_top
	/\ box_text_rects[b].x2 = box_text_rects[b].x1 + box_text_size[b].width
	/\ box_text_rects[b].y2 = box_text_rects[b].y1 + box_text_size[b].height
	/\ boxes[b].x2 - boxes[b].x1 >= (box_text_rects[b].x2 - box_text_rects[b].x1) + padding.box_text_right_extra
);

% Primitive fixed-size constraints from /docker-files/worker/code/ElementGroup_gurobi.py:22-25.
constraint forall(p in Primitive) (
	primitives[p].x2 - primitives[p].x1 = primitive_size[p].width
	/\ primitives[p].y2 - primitives[p].y1 = primitive_size[p].height
);

% Primitive containment inside its boxes from /docker-files/worker/code/Box_gurobi.py:37-43.
% The Python data builder reproduces the later removePrimitiveConstrains() calls
% triggered by subset boxes in /docker-files/worker/code/ModelConstraints.py:42-60.
constraint forall(b in Box, p in Primitive where require_primitive_containment[b, p]) (
	primitives[p].x1 - boxes[b].x1 >= padding.box_inner
	/\ primitives[p].y1 - boxes[b].y1 >= max(padding.box_min_top, box_text_size[b].height + padding.box_inner)
	/\ boxes[b].x2 - primitives[p].x2 >= padding.box_inner
	/\ boxes[b].y2 - primitives[p].y2 >= padding.box_inner
);

% Global bounding-box coverage from /docker-files/worker/code/main.py:202-206.
constraint forall(b in Box) (
	global_box.x1 <= boxes[b].x1
	/\ global_box.y1 <= boxes[b].y1
	/\ global_box.x2 >= boxes[b].x2
	/\ global_box.y2 >= boxes[b].y2
);

% Box-subset constraints from /docker-files/worker/code/ModelConstraints.py:41-59.
% If box_subset[outer, inner] is true, then inner must sit strictly inside outer.
constraint forall(outer, inner in Box where outer != inner /\ box_subset[outer, inner]) (
	boxes[outer].x1 <= boxes[inner].x1 - distance.box
	/\ boxes[outer].y1 <= boxes[inner].y1 - distance.box - box_text_size[outer].height
	/\ boxes[outer].x2 - distance.box >= boxes[inner].x2
	/\ boxes[outer].y2 - distance.box >= boxes[inner].y2
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
	primitives[p].x2 + distance.primitive <= boxes[b].x1
	\/ primitives[p].y2 + distance.primitive <= boxes[b].y1
	\/ boxes[b].x2 + distance.primitive <= primitives[p].x1
	\/ boxes[b].y2 + distance.primitive <= primitives[p].y1
);

% Set-name non-overlap from /docker-files/worker/code/ModelConstraints.py:63-82.
% Original formulation again used four binaries plus big-M; this keeps the same
% four-way separation as a direct logical disjunction.
constraint forall(b1, b2 in Box where b1 < b2) (
	box_text_rects[b1].x2 + distance.primitive <= box_text_rects[b2].x1
	\/ box_text_rects[b1].y2 + distance.primitive <= box_text_rects[b2].y1
	\/ box_text_rects[b2].x2 + distance.primitive <= box_text_rects[b1].x1
	\/ box_text_rects[b2].y2 + distance.primitive <= box_text_rects[b1].y1
);

% Non-overlap for disjoint boxes from /docker-files/worker/code/ModelConstraints.py:84-107.
% The original used the same four-binary big-M pattern; MiniZinc uses a direct
% disjunction of the four relative placements.
constraint forall(b1, b2 in Box where b1 < b2 /\ prevent_box_overlap[b1, b2]) (
	boxes[b1].x2 + distance.primitive <= boxes[b2].x1
	\/ boxes[b1].y2 + distance.primitive <= boxes[b2].y1
	\/ boxes[b2].x2 + distance.primitive <= boxes[b1].x1
	\/ boxes[b2].y2 + distance.primitive <= boxes[b1].y1
);

% Edge-distance constraints for overlapping, non-nested boxes from
% /docker-files/worker/code/ModelConstraints.py:109-160.
% Original Gurobi formulation linearised each absolute value with a dedicated
% binary and big-M pair of inequalities. MiniZinc can state the intended form
% directly as abs(edge_a - edge_b) >= box_dist.
constraint forall(b1, b2 in Box where b1 < b2 /\ require_box_distance[b1, b2]) (
	abs(boxes[b1].x2 - boxes[b2].x1) >= distance.box
	/\ abs(boxes[b1].x1 - boxes[b2].x1) >= distance.box
	/\ abs(boxes[b1].x2 - boxes[b2].x2) >= distance.box
	/\ abs(boxes[b2].x2 - boxes[b1].x1) >= distance.box
	/\ abs(boxes[b1].y2 - boxes[b2].y1) >= distance.box
	/\ abs(boxes[b1].y1 - boxes[b2].y1) >= distance.box
	/\ abs(boxes[b1].y2 - boxes[b2].y2) >= distance.box
	/\ abs(boxes[b2].y2 - boxes[b1].y1) >= distance.box
);

% Objective from /docker-files/worker/code/main.py:214-216.
% This minimizes box perimeters-ish extents plus the enclosing box size and z.
solve minimize
	sum(b in Box)((boxes[b].x2 - boxes[b].x1) + (boxes[b].y2 - boxes[b].y1))
	+ (global_box.x2 - global_box.x1)
	+ (global_box.y2 - global_box.y1)
	+ z;
