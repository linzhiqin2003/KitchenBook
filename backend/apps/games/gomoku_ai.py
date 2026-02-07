"""
Gomoku AI engine – Minimax with Alpha-Beta pruning.

Pure functions, no state.  Safe to call from ``asyncio.to_thread``.
"""

BOARD_SIZE = 15
WIN_LENGTH = 5

# (consecutive, open_ends) → score
_SCORE_TABLE = {
    (5, 0): 100_000,
    (5, 1): 100_000,
    (5, 2): 100_000,
    (4, 2): 10_000,   # 活四
    (4, 1): 1_000,    # 冲四
    (3, 2): 1_000,    # 活三
    (3, 1): 100,      # 眠三
    (2, 2): 100,      # 活二
    (2, 1): 10,       # 眠二
    (1, 2): 1,
    (1, 1): 0,
}

_DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]


def _in_bounds(x, y):
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE


def _get_candidates(board, distance=2):
    """Return empty positions within Manhattan *distance* of any existing stone."""
    occupied = set()
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] != 0:
                occupied.add((x, y))

    if not occupied:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

    candidates = set()
    for ox, oy in occupied:
        for dy in range(-distance, distance + 1):
            for dx in range(-distance, distance + 1):
                nx, ny = ox + dx, oy + dy
                if _in_bounds(nx, ny) and board[ny][nx] == 0:
                    candidates.add((nx, ny))
    return list(candidates)


def _evaluate_line(board, x, y, dx, dy, stone):
    """Count consecutive *stone* starting at (x,y) in direction (dx,dy),
    and how many ends are open.  Returns (count, open_ends)."""
    count = 0
    cx, cy = x, y
    while _in_bounds(cx, cy) and board[cy][cx] == stone:
        count += 1
        cx += dx
        cy += dy

    open_ends = 0
    # check end after the run
    if _in_bounds(cx, cy) and board[cy][cx] == 0:
        open_ends += 1
    # check end before the start
    bx, by = x - dx, y - dy
    if _in_bounds(bx, by) and board[by][bx] == 0:
        open_ends += 1

    return count, open_ends


def _evaluate_board(board, ai_stone):
    """Heuristic board evaluation from *ai_stone*'s perspective."""
    opp = 3 - ai_stone
    ai_score = 0
    opp_score = 0

    visited_ai = set()
    visited_opp = set()

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            for dx, dy in _DIRECTIONS:
                if board[y][x] == ai_stone and (x, y, dx, dy) not in visited_ai:
                    count, open_ends = _evaluate_line(board, x, y, dx, dy, ai_stone)
                    # mark all positions in this line as visited for this direction
                    for i in range(count):
                        visited_ai.add((x + dx * i, y + dy * i, dx, dy))
                    ai_score += _SCORE_TABLE.get((count, open_ends), 0)

                if board[y][x] == opp and (x, y, dx, dy) not in visited_opp:
                    count, open_ends = _evaluate_line(board, x, y, dx, dy, opp)
                    for i in range(count):
                        visited_opp.add((x + dx * i, y + dy * i, dx, dy))
                    opp_score += _SCORE_TABLE.get((count, open_ends), 0)

    return ai_score - opp_score * 1.1


def _quick_score(board, x, y, stone):
    """Fast heuristic score for a single move (used to rank candidates)."""
    opp = 3 - stone
    score = 0
    board[y][x] = stone
    for dx, dy in _DIRECTIONS:
        # score for our stone
        sx, sy = x, y
        while _in_bounds(sx - dx, sy - dy) and board[sy - dy][sx - dx] == stone:
            sx -= dx
            sy -= dy
        count, open_ends = _evaluate_line(board, sx, sy, dx, dy, stone)
        score += _SCORE_TABLE.get((count, open_ends), 0)

    board[y][x] = opp
    for dx, dy in _DIRECTIONS:
        sx, sy = x, y
        while _in_bounds(sx - dx, sy - dy) and board[sy - dy][sx - dx] == opp:
            sx -= dx
            sy -= dy
        count, open_ends = _evaluate_line(board, sx, sy, dx, dy, opp)
        score += _SCORE_TABLE.get((count, open_ends), 0) * 0.9

    board[y][x] = 0
    return score


def _check_five(board, x, y, stone):
    """Return True if placing *stone* at (x,y) creates five-in-a-row."""
    board[y][x] = stone
    won = False
    for dx, dy in _DIRECTIONS:
        count = 1
        for sign in (1, -1):
            cx, cy = x + dx * sign, y + dy * sign
            while _in_bounds(cx, cy) and board[cy][cx] == stone:
                count += 1
                cx += dx * sign
                cy += dy * sign
        if count >= WIN_LENGTH:
            won = True
            break
    board[y][x] = 0
    return won


def _minimax(board, depth, alpha, beta, is_maximizing, ai_stone, max_candidates):
    """Minimax with alpha-beta pruning."""
    candidates = _get_candidates(board, distance=2)
    if not candidates or depth == 0:
        return _evaluate_board(board, ai_stone), None

    current_stone = ai_stone if is_maximizing else (3 - ai_stone)

    # sort candidates by heuristic for better pruning
    scored = [(c, _quick_score(board, c[0], c[1], current_stone)) for c in candidates]
    scored.sort(key=lambda t: t[1], reverse=True)
    top_candidates = [c for c, _ in scored[:max_candidates]]

    best_move = top_candidates[0]

    if is_maximizing:
        max_eval = float("-inf")
        for x, y in top_candidates:
            # instant win check
            if _check_five(board, x, y, current_stone):
                return 100_000 + depth, (x, y)
            board[y][x] = current_stone
            eval_score, _ = _minimax(board, depth - 1, alpha, beta, False, ai_stone, max_candidates)
            board[y][x] = 0
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (x, y)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float("inf")
        for x, y in top_candidates:
            if _check_five(board, x, y, current_stone):
                return -(100_000 + depth), (x, y)
            board[y][x] = current_stone
            eval_score, _ = _minimax(board, depth - 1, alpha, beta, True, ai_stone, max_candidates)
            board[y][x] = 0
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (x, y)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move


def find_best_move(board, color, max_depth=4, max_candidates=10):
    """
    Find the best move for *color* (``"black"`` or ``"white"``).

    Parameters
    ----------
    board : list[list[int]]
        15×15 board, 0=empty, 1=black, 2=white.
    color : str
        ``"black"`` or ``"white"``.
    max_depth : int
        Search depth (default 4).
    max_candidates : int
        Top-N candidates per level (default 10).

    Returns
    -------
    tuple[int, int]
        ``(x, y)`` of recommended move.
    """
    ai_stone = 1 if color == "black" else 2
    opp_stone = 3 - ai_stone

    candidates = _get_candidates(board, distance=2)
    if not candidates:
        c = BOARD_SIZE // 2
        return (c, c)

    # 1) Instant win
    for x, y in candidates:
        if _check_five(board, x, y, ai_stone):
            return (x, y)

    # 2) Block opponent win
    for x, y in candidates:
        if _check_five(board, x, y, opp_stone):
            return (x, y)

    # 3) Minimax search
    _score, move = _minimax(
        board, max_depth, float("-inf"), float("inf"),
        True, ai_stone, max_candidates,
    )

    if move is None:
        return candidates[0]
    return move
