import copy



root = {"used": False, "pos": [0, 0], "size": [100, 100], 'down': None, 'right': None}


def pack(sizes):
    global root
    root = {"used": False, "pos": [0, 0], "size": [sizes[0][0], sizes[0][1]], 'down': None, 'right': None}

    blocks = []

    for s in sizes:
        block = {"size": s}
        blocks.append(block)

    for block in blocks:

        node = findNode(root, block["size"])
        if node is not None:
            block["pos"] = splitNode(node, block["size"])
        else:
            block["pos"] = growNode(block["size"][0], block["size"][1])


    retvals = [x["pos"] for x in blocks]
    return retvals


def findNode(node, size):
    if node is None:
        return None
    if node["used"]:
        right = findNode(node["right"], size)
        if right is not None:
            return right

        down = findNode(node["down"], size)
        if down is not None:
            return down
    else:
        if (size[0] <= node["size"][0]) and (size[1] <= node["size"][1]):
            return node
        else:
            return None


def splitNode(node, size):
    node["used"] = True
    node["down"] = {"used": False, "pos": [node["pos"][0], node["pos"][1] + size[1]], "size": [node["size"][0], node["size"][1] - size[1]], 'down': None, 'right': None}
    node["right"] = {"used": False, "pos": [node["pos"][0] + size[0], node["pos"][1]], "size": [node["size"][0] - size[0], size[1]], 'down': None, 'right': None}
    return node['pos']


def growNode(w, h):
    global root
    canGrowDown = (w <= root["size"][0])
    canGrowRight = (h <= root["size"][1])

    shouldGrowRight = canGrowRight and (root["size"][1] >= (root["size"][0] + w))
    shouldGrowDown = canGrowDown and (root["size"][0] >= (root["size"][1] + h))

    if shouldGrowRight:
        return growRight(w, h)
    else:
        if shouldGrowDown:
            return growDown(w, h)
        else:
            if canGrowRight:
                return growRight(w, h)
            else:
                if canGrowDown:
                    return growDown(w, h)
                else:
                    return None


def growRight(w, h):
    global root
    original_root = copy.deepcopy(root)

    root["used"] = True
    root["size"] = [root["size"][0] + w, root["size"][1]]
    root["right"] = {"used": False, 'pos': [original_root['size'][0], 0], 'size': [w, root["size"][1]], 'down': None, 'right': None}
    root["down"] = original_root

    node = findNode(root, [w, h])
    if node is not None:
        return splitNode(node, [w, h])
    else:
        return None


def growDown(w, h):
    global root
    original_root = copy.deepcopy(root)
    root["used"] = True
    root["size"] = [root["size"][0], root["size"][1]+h]
    root["down"] = {"used": False, 'pos': [0, original_root['size'][1]], 'size': [root["size"][0], h], 'down': None, 'right': None}
    root["right"] = original_root

    node = findNode(root, [w, h])
    if node is not None:
        return splitNode(node, [w, h])
    else:
        return None


if __name__=='__main__':
    sizes = [
        [3,1],
        [2, 2],
        [4,3],
        [5,2]
    ]

    sizes = sorted(sizes, key=lambda size: max(size[0], size[1]), reverse=True)
    pos = pack(sizes)
    print(sizes)
    print(pos)