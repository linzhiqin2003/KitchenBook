"""
Gomoku AI engine with stronger tactical and search capability.

Key upgrades over the previous version:
1. Iterative-deepening alpha-beta search (soft time limit).
2. Transposition table for deeper practical lookahead.
3. Tactical pre-checks: instant win/block + double-threat detection.
4. Better position evaluation for open four / double-three pressure.
5. Symmetry-aware opening book for early game.

Pure functions, no shared mutable global state. Safe for ``asyncio.to_thread``.
"""

from __future__ import annotations

import time
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

BOARD_SIZE = 15
WIN_LENGTH = 5

WIN_SCORE = 10_000_000
NEG_INF = -10**18
POS_INF = 10**18

# (consecutive, open_ends) -> score
_SCORE_TABLE = {
    (5, 0): WIN_SCORE,
    (5, 1): WIN_SCORE,
    (5, 2): WIN_SCORE,
    (4, 2): 450_000,   # open four
    (4, 1): 45_000,    # closed four
    (3, 2): 10_000,    # open three
    (3, 1): 900,       # closed three
    (2, 2): 160,       # open two
    (2, 1): 20,        # closed two
    (1, 2): 4,
    (1, 1): 0,
}

_DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))

_TT_EXACT = 0
_TT_LOWER = 1
_TT_UPPER = 2

_TRANSFORM_INVERSE = (0, 3, 2, 1, 4, 5, 6, 7)
_OPENING_BOOK_MAX_STONES = 4

# (side_to_move, stones, moves)
# stones: (dx, dy, stone), moves: (dx, dy), all relative to center.
_OPENING_BOOK_PATTERNS = (
    # White's first move against black center.
    (2, ((0, 0, 1),), ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1))),
    # Black's second move when white responds orthogonally.
    (1, ((0, 0, 1), (1, 0, 2)), ((0, 1), (0, -1), (-1, 0), (1, 1), (1, -1))),
    # Black's second move when white responds diagonally.
    (1, ((0, 0, 1), (1, 1, 2)), ((1, 0), (0, 1), (-1, 0), (0, -1), (2, 0))),
)

_RNG = random.Random(20260207)
_ZOBRIST = [
    [[_RNG.getrandbits(64) for _ in range(3)] for _x in range(BOARD_SIZE)]
    for _y in range(BOARD_SIZE)
]


@dataclass
class _TTEntry:
    depth: int
    score: int
    flag: int
    move: Optional[Tuple[int, int]]


class _SearchTimeout(Exception):
    pass


def _in_bounds(x: int, y: int) -> bool:
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE


def _transform_xy(x: int, y: int, transform_id: int) -> Tuple[int, int]:
    n = BOARD_SIZE - 1
    if transform_id == 0:   # identity
        return x, y
    if transform_id == 1:   # rot90
        return n - y, x
    if transform_id == 2:   # rot180
        return n - x, n - y
    if transform_id == 3:   # rot270
        return y, n - x
    if transform_id == 4:   # mirror vertical axis
        return n - x, y
    if transform_id == 5:   # mirror + rot90
        return n - y, n - x
    if transform_id == 6:   # mirror + rot180
        return x, n - y
    if transform_id == 7:   # mirror + rot270
        return y, x
    raise ValueError(f"unknown transform_id={transform_id}")


def _canonical_opening_key(
    side_to_move: int, stones: Sequence[Tuple[int, int, int]]
) -> Tuple[Tuple[int, Tuple[Tuple[int, int, int], ...]], int]:
    best_key = None
    best_transform = 0
    for transform_id in range(8):
        transformed = tuple(
            sorted(
                (tx, ty, stone)
                for x, y, stone in stones
                for tx, ty in [_transform_xy(x, y, transform_id)]
            )
        )
        key = (side_to_move, transformed)
        if best_key is None or key < best_key:
            best_key = key
            best_transform = transform_id
    return best_key, best_transform


def _build_opening_book() -> Dict[Tuple[int, Tuple[Tuple[int, int, int], ...]], Tuple[Tuple[int, int], ...]]:
    center = BOARD_SIZE // 2
    book: Dict[Tuple[int, Tuple[Tuple[int, int, int], ...]], Tuple[Tuple[int, int], ...]] = {}

    for side_to_move, rel_stones, rel_moves in _OPENING_BOOK_PATTERNS:
        abs_stones = []
        for dx, dy, stone in rel_stones:
            x, y = center + dx, center + dy
            if not _in_bounds(x, y):
                abs_stones = []
                break
            abs_stones.append((x, y, stone))
        if not abs_stones:
            continue

        canonical_key, transform_id = _canonical_opening_key(side_to_move, abs_stones)

        canonical_moves = []
        seen = set()
        for dx, dy in rel_moves:
            x, y = center + dx, center + dy
            if not _in_bounds(x, y):
                continue
            mx, my = _transform_xy(x, y, transform_id)
            if not _in_bounds(mx, my):
                continue
            if (mx, my) in seen:
                continue
            seen.add((mx, my))
            canonical_moves.append((mx, my))

        if canonical_moves:
            book[canonical_key] = tuple(canonical_moves)

    return book


_OPENING_BOOK = _build_opening_book()


def _center_bias(x: int, y: int) -> int:
    c = BOARD_SIZE // 2
    return BOARD_SIZE - (abs(x - c) + abs(y - c))


def _opening_book_move(board: List[List[int]], side_to_move: int) -> Optional[Tuple[int, int]]:
    stones = [
        (x, y, board[y][x])
        for y in range(BOARD_SIZE)
        for x in range(BOARD_SIZE)
        if board[y][x] != 0
    ]
    if len(stones) > _OPENING_BOOK_MAX_STONES:
        return None

    canonical_key, transform_id = _canonical_opening_key(side_to_move, stones)
    canonical_moves = _OPENING_BOOK.get(canonical_key)
    if not canonical_moves:
        return None

    inverse_transform = _TRANSFORM_INVERSE[transform_id]
    for mx, my in canonical_moves:
        x, y = _transform_xy(mx, my, inverse_transform)
        if _in_bounds(x, y) and board[y][x] == 0:
            return (x, y)
    return None


def _board_hash(board: Sequence[Sequence[int]]) -> int:
    h = 0
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            stone = board[y][x]
            if stone:
                h ^= _ZOBRIST[y][x][stone]
    return h


def _get_candidates(board: Sequence[Sequence[int]], distance: int = 2) -> List[Tuple[int, int]]:
    """Return empty positions within Chebyshev *distance* of existing stones."""
    occupied = []
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] != 0:
                occupied.append((x, y))

    if not occupied:
        c = BOARD_SIZE // 2
        return [(c, c)]

    candidates = set()
    for ox, oy in occupied:
        for dy in range(-distance, distance + 1):
            for dx in range(-distance, distance + 1):
                nx, ny = ox + dx, oy + dy
                if _in_bounds(nx, ny) and board[ny][nx] == 0:
                    candidates.add((nx, ny))

    return list(candidates)


def _evaluate_line(
    board: Sequence[Sequence[int]], x: int, y: int, dx: int, dy: int, stone: int
) -> Tuple[int, int]:
    """Count consecutive stones from (x,y) and number of open ends."""
    count = 0
    cx, cy = x, y
    while _in_bounds(cx, cy) and board[cy][cx] == stone:
        count += 1
        cx += dx
        cy += dy

    open_ends = 0
    if _in_bounds(cx, cy) and board[cy][cx] == 0:
        open_ends += 1
    bx, by = x - dx, y - dy
    if _in_bounds(bx, by) and board[by][bx] == 0:
        open_ends += 1
    return count, open_ends


def _evaluate_for_stone(board: Sequence[Sequence[int]], stone: int) -> Tuple[int, int, int]:
    """Return (score, open_fours, open_threes) for one side."""
    score = 0
    open_fours = 0
    open_threes = 0

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] != stone:
                continue
            for dx, dy in _DIRECTIONS:
                px, py = x - dx, y - dy
                # only evaluate line starts to avoid duplicate counting
                if _in_bounds(px, py) and board[py][px] == stone:
                    continue

                count, open_ends = _evaluate_line(board, x, y, dx, dy, stone)
                if count >= WIN_LENGTH:
                    return WIN_SCORE, open_fours, open_threes

                score += _SCORE_TABLE.get((count, open_ends), 0)
                if count == 4 and open_ends == 2:
                    open_fours += 1
                elif count == 3 and open_ends == 2:
                    open_threes += 1

    score += open_fours * 130_000
    if open_threes >= 2:
        score += 60_000 + (open_threes - 2) * 18_000
    elif open_threes == 1:
        score += 8_000

    return score, open_fours, open_threes


def _evaluate_board(board: List[List[int]], perspective_stone: int) -> int:
    """Heuristic board evaluation from *perspective_stone*'s perspective."""
    opp = 3 - perspective_stone
    own_score, own_open_four, own_open_three = _evaluate_for_stone(board, perspective_stone)
    opp_score, opp_open_four, opp_open_three = _evaluate_for_stone(board, opp)

    if own_score >= WIN_SCORE:
        return WIN_SCORE
    if opp_score >= WIN_SCORE:
        return -WIN_SCORE

    score = own_score - int(opp_score * 1.08)

    if own_open_four and own_open_three:
        score += 120_000
    if opp_open_four and opp_open_three:
        score -= 140_000

    return int(score)


def _quick_score(board: List[List[int]], x: int, y: int, stone: int) -> int:
    """Fast local heuristic for move ordering."""
    if board[y][x] != 0:
        return NEG_INF

    opp = 3 - stone
    score = _center_bias(x, y) * 12

    # Instant tactical priorities
    if _check_five(board, x, y, stone):
        return WIN_SCORE // 2 + score
    if _check_five(board, x, y, opp):
        score += WIN_SCORE // 3

    board[y][x] = stone
    for dx, dy in _DIRECTIONS:
        sx, sy = x, y
        while _in_bounds(sx - dx, sy - dy) and board[sy - dy][sx - dx] == stone:
            sx -= dx
            sy -= dy
        count, open_ends = _evaluate_line(board, sx, sy, dx, dy, stone)
        score += _SCORE_TABLE.get((count, open_ends), 0)
    board[y][x] = 0

    return int(score)


def _check_five(board: List[List[int]], x: int, y: int, stone: int) -> bool:
    """Return True if placing *stone* at (x,y) creates five-in-a-row."""
    if board[y][x] != 0:
        return False

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


def _pick_best_by_quick(
    board: List[List[int]], candidates: Sequence[Tuple[int, int]], stone: int
) -> Tuple[int, int]:
    best = candidates[0]
    best_score = NEG_INF
    for x, y in candidates:
        s = _quick_score(board, x, y, stone)
        if s > best_score:
            best_score = s
            best = (x, y)
    return best


def _ordered_candidates(
    board: List[List[int]],
    stone: int,
    limit: int,
    preferred: Optional[Tuple[int, int]] = None,
) -> List[Tuple[int, int]]:
    candidates = _get_candidates(board, distance=2)
    if not candidates:
        return []

    scored = [((x, y), _quick_score(board, x, y, stone)) for x, y in candidates]
    scored.sort(key=lambda item: item[1], reverse=True)
    ordered = [move for move, _ in scored]

    if preferred and preferred in ordered:
        ordered.remove(preferred)
        ordered.insert(0, preferred)

    return ordered[: max(1, min(limit, len(ordered)))]


def _find_immediate_wins(
    board: List[List[int]], stone: int, candidates: Sequence[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    return [(x, y) for x, y in candidates if _check_five(board, x, y, stone)]


def _find_double_win_moves(
    board: List[List[int]],
    stone: int,
    candidates: Sequence[Tuple[int, int]],
    probe_limit: int = 12,
) -> List[Tuple[int, int]]:
    """
    Find moves that create >=2 immediate winning continuations next turn.
    This catches many practical "double threat" (fork) patterns.
    """
    if not candidates:
        return []

    scored = [((x, y), _quick_score(board, x, y, stone)) for x, y in candidates]
    scored.sort(key=lambda item: item[1], reverse=True)
    probe_moves = [move for move, _ in scored[: min(probe_limit, len(scored))]]

    forks = []
    for x, y in probe_moves:
        if board[y][x] != 0:
            continue
        board[y][x] = stone
        next_candidates = _get_candidates(board, distance=2)
        wins = 0
        for nx, ny in next_candidates:
            if _check_five(board, nx, ny, stone):
                wins += 1
                if wins >= 2:
                    forks.append((x, y))
                    break
        board[y][x] = 0
    return forks


def _check_timeout(start_time: float, time_limit: Optional[float]) -> None:
    if time_limit is None or time_limit <= 0:
        return
    if (time.perf_counter() - start_time) >= time_limit:
        raise _SearchTimeout


def _negamax(
    board: List[List[int]],
    depth: int,
    alpha: int,
    beta: int,
    stone: int,
    zobrist_key: int,
    max_candidates: int,
    root_depth: int,
    start_time: float,
    time_limit: Optional[float],
    transposition: Dict[Tuple[int, int], _TTEntry],
) -> Tuple[int, Optional[Tuple[int, int]]]:
    _check_timeout(start_time, time_limit)

    if depth == 0:
        return _evaluate_board(board, stone), None

    all_candidates = _get_candidates(board, distance=2)
    if not all_candidates:
        return 0, None

    # Tactical shortcut: if current side can win now, no need to search deeper.
    for x, y in all_candidates:
        if _check_five(board, x, y, stone):
            return WIN_SCORE - (root_depth - depth), (x, y)

    original_alpha = alpha
    original_beta = beta
    tt_key = (stone, zobrist_key)
    entry = transposition.get(tt_key)
    preferred_move = None

    if entry and entry.depth >= depth:
        preferred_move = entry.move
        if entry.flag == _TT_EXACT:
            return entry.score, entry.move
        if entry.flag == _TT_LOWER:
            alpha = max(alpha, entry.score)
        elif entry.flag == _TT_UPPER:
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score, entry.move
    elif entry:
        preferred_move = entry.move

    ply = root_depth - depth
    candidate_limit = max(6, max_candidates - ply * 2)
    moves = _ordered_candidates(board, stone, candidate_limit, preferred=preferred_move)
    if not moves:
        return _evaluate_board(board, stone), None

    best_score = NEG_INF
    best_move = moves[0]
    opp = 3 - stone

    for x, y in moves:
        _check_timeout(start_time, time_limit)
        if board[y][x] != 0:
            continue

        board[y][x] = stone
        try:
            child_hash = zobrist_key ^ _ZOBRIST[y][x][stone]
            child_score, _ = _negamax(
                board,
                depth=depth - 1,
                alpha=-beta,
                beta=-alpha,
                stone=opp,
                zobrist_key=child_hash,
                max_candidates=max_candidates,
                root_depth=root_depth,
                start_time=start_time,
                time_limit=time_limit,
                transposition=transposition,
            )
        finally:
            # Timeout or recursion errors must not leave residual stones on board.
            board[y][x] = 0

        score = -child_score
        if score > best_score:
            best_score = score
            best_move = (x, y)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best_score <= original_alpha:
        flag = _TT_UPPER
    elif best_score >= original_beta:
        flag = _TT_LOWER
    else:
        flag = _TT_EXACT

    transposition[tt_key] = _TTEntry(depth=depth, score=best_score, flag=flag, move=best_move)
    return best_score, best_move


def find_best_move(
    board: List[List[int]],
    color: str,
    max_depth: int = 7,
    max_candidates: int = 16,
    time_limit: Optional[float] = 2.4,
) -> Tuple[int, int]:
    """
    Find best move for ``color`` (``"black"`` or ``"white"``).

    Defaults are tuned for stronger practical play while keeping hint response
    reasonably fast in online matches.
    """
    ai_stone = 1 if color == "black" else 2
    opp_stone = 3 - ai_stone

    candidates = _get_candidates(board, distance=2)
    if not candidates:
        c = BOARD_SIZE // 2
        return (c, c)

    # 1) Instant win
    winning_moves = _find_immediate_wins(board, ai_stone, candidates)
    if winning_moves:
        return _pick_best_by_quick(board, winning_moves, ai_stone)

    # 2) Instant block
    block_moves = _find_immediate_wins(board, opp_stone, candidates)
    if block_moves:
        return _pick_best_by_quick(board, block_moves, ai_stone)

    # 3) Opening book (first several plies, symmetry-aware).
    book_move = _opening_book_move(board, ai_stone)
    if book_move is not None:
        return book_move

    # 4) Create own double threat if available
    fork_moves = _find_double_win_moves(board, ai_stone, candidates)
    if fork_moves:
        return _pick_best_by_quick(board, fork_moves, ai_stone)

    # 5) Block opponent double threat if detected
    opp_fork_moves = _find_double_win_moves(board, opp_stone, candidates)
    if opp_fork_moves:
        return _pick_best_by_quick(board, opp_fork_moves, ai_stone)

    # 6) Iterative deepening search with transposition table
    fallback = _pick_best_by_quick(board, candidates, ai_stone)
    best_move = fallback
    transposition: Dict[Tuple[int, int], _TTEntry] = {}
    root_hash = _board_hash(board)

    start_time = time.perf_counter()
    for depth in range(1, max_depth + 1):
        try:
            score, move = _negamax(
                board,
                depth=depth,
                alpha=NEG_INF,
                beta=POS_INF,
                stone=ai_stone,
                zobrist_key=root_hash,
                max_candidates=max_candidates,
                root_depth=depth,
                start_time=start_time,
                time_limit=time_limit,
                transposition=transposition,
            )
        except _SearchTimeout:
            break

        if move is not None:
            best_move = move

        if score >= WIN_SCORE // 2:
            break

    return best_move
