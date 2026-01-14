EMPTY, HUMAN, AI = ' ', 'O', 'X'

def create_board():
    return [[EMPTY]*3 for _ in range(3)]

def print_board(b):
    for i in range(3):
        print(' | '.join(b[i]))
        if i < 2: print('-'*9)

def winner(b):
    lines = (
        b[0], b[1], b[2],
        [b[0][0], b[1][0], b[2][0]],
        [b[0][1], b[1][1], b[2][1]],
        [b[0][2], b[1][2], b[2][2]],
        [b[0][0], b[1][1], b[2][2]],
        [b[0][2], b[1][1], b[2][0]]
    )
    for line in lines:
        if line[0] == line[1] == line[2] != EMPTY:
            return line[0]
    return 'DRAW' if all(c != EMPTY for r in b for c in r) else None

def dfs(b, player):
    res = winner(b)
    if res == AI: return 1
    if res == HUMAN: return -1
    if res == 'DRAW': return 0

    best = -2 if player == AI else 2
    for i in range(3):
        for j in range(3):
            if b[i][j] == EMPTY:
                b[i][j] = player
                val = dfs(b, HUMAN if player == AI else AI)
                b[i][j] = EMPTY
                if player == AI:
                    best = max(best, val)
                else:
                    best = min(best, val)
    return best

def best_move(b):
    best, move = -2, None
    for i in range(3):
        for j in range(3):
            if b[i][j] == EMPTY:
                b[i][j] = AI
                val = dfs(b, HUMAN)
                b[i][j] = EMPTY
                if val > best:
                    best, move = val, (i, j)
    return move

def human_move(b):
    while True:
        p = int(input("Your move (1-9): ")) - 1
        r, c = divmod(p, 3)
        if 0 <= p < 9 and b[r][c] == EMPTY:
            b[r][c] = HUMAN
            break
        print("Invalid move.")

def play():
    b = create_board()
    turn = HUMAN
    while True:
        print_board(b)
        if turn == HUMAN:
            human_move(b)
            turn = AI
        else:
            r, c = best_move(b)
            b[r][c] = AI
            turn = HUMAN
        res = winner(b)
        if res:
            print_board(b)
            print("Result:", "DRAW" if res == 'DRAW' else f"{res} wins")
            break

if __name__ == "__main__":
    play()
