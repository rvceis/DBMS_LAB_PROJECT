import math

def minimax(i, depth, alpha, beta, maximizing, tree):
    # i: index in full tree array (root = 0)
    # depth: remaining depth from this node
    # terminating condition
    if depth == 0:
        return tree[i]

    if maximizing:
        maxEva = -math.inf
        for child in (2*i + 1, 2*i + 2):
            eva = minimax(child, depth - 1, alpha, beta, False, tree)
            maxEva = max(maxEva, eva)
            alpha = max(alpha, maxEva)
            if beta <= alpha:
                break
        return maxEva
    else:
        minEva = math.inf
        for child in (2*i + 1, 2*i + 2):
            eva = minimax(child, depth - 1, alpha, beta, True, tree)
            minEva = min(minEva, eva)
            beta = min(beta, minEva)
            if beta <= alpha:
                break
        return minEva

if __name__ == "__main__":
    import math

    depth = int(input("Enter depth of full binary tree (e.g., 3): "))
    leaf_count = 2 ** depth

    print(f"Enter {leaf_count} leaf values separated by space:")
    leaves = list(map(int, input().split()))
    if len(leaves) != leaf_count:
        raise ValueError("Number of values does not match 2^depth")

    # build full tree array: internal nodes placeholders + leaves
    total_nodes = 2 ** (depth + 1) - 1
    tree = [0] * total_nodes
    start_leaves = total_nodes - leaf_count
    tree[start_leaves:] = leaves

    value = minimax(0, depth, -math.inf, math.inf, True, tree)
    print("Evaluated Value:", value)
