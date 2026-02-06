"""
WebSocket consumer for room-based Gomoku.

Supports:
- Two players (black / white)
- Unlimited spectators
- Realtime room/global online statistics

State is kept in process memory. For multi-instance deployments, move room
state and counters to Redis or a database-backed design.
"""

import json
import re
import threading
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer

BOARD_SIZE = 15
ROOM_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
MAX_NICKNAME_LENGTH = 20


def _create_empty_board():
    return [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def _normalize_nickname(raw_name):
    if not raw_name:
        return "Guest"
    value = raw_name.strip()
    if not value:
        return "Guest"
    return value[:MAX_NICKNAME_LENGTH]


class GomokuConsumer(AsyncWebsocketConsumer):
    """
    Two-player Gomoku with spectators.

    Client messages:
    - {"type":"move","x":3,"y":4}
    - {"type":"restart"}
    - {"type":"ping"}

    Server messages:
    - joined
    - room_state
    - error
    - pong
    """

    rooms = {}
    rooms_lock = threading.Lock()
    active_connections = set()

    async def send_json(self, payload):
        """
        Lightweight JSON sender for AsyncWebsocketConsumer.
        """
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    async def connect(self):
        room_id = (self.scope.get("url_route", {}).get("kwargs", {}).get("room_id", "") or "").upper()
        if not ROOM_ID_PATTERN.match(room_id):
            await self.close(code=4000)
            return

        query_params = parse_qs((self.scope.get("query_string") or b"").decode("utf-8"))
        nickname = _normalize_nickname((query_params.get("name") or ["Guest"])[0])

        self.room_id = room_id
        self.nickname = nickname
        self.group_name = f"gomoku_{self.room_id}"
        self.player_color = None
        self.role = "spectator"

        with self.rooms_lock:
            room = self.rooms.setdefault(self.room_id, self._create_room())
            self.active_connections.add(self.channel_name)
            assigned_color = self._assign_player(room, self.channel_name, self.nickname)

            if assigned_color:
                self.role = "player"
                self.player_color = assigned_color
            else:
                room["spectators"][self.channel_name] = {
                    "channel_name": self.channel_name,
                    "nickname": self.nickname,
                }

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send_json(
            {
                "type": "joined",
                "roomId": self.room_id,
                "role": self.role,
                "playerColor": self.player_color,
                "nickname": self.nickname,
            }
        )
        await self._broadcast_room_state(reason="join")

    async def disconnect(self, close_code):
        if not getattr(self, "room_id", None):
            return

        should_broadcast = False
        with self.rooms_lock:
            self.active_connections.discard(self.channel_name)

            room = self.rooms.get(self.room_id)
            if room:
                removed_player = self._remove_player(room, self.channel_name)
                removed_spectator = room["spectators"].pop(self.channel_name, None) is not None

                if removed_player:
                    self._reset_board(room)
                    room["status"] = "waiting"

                room_is_empty = (
                    room["players"]["black"] is None
                    and room["players"]["white"] is None
                    and not room["spectators"]
                )
                if room_is_empty:
                    self.rooms.pop(self.room_id, None)
                else:
                    should_broadcast = removed_player or removed_spectator

        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if should_broadcast:
            await self._broadcast_room_state(reason="leave")

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "无效的 JSON 消息。"})
            return

        msg_type = payload.get("type")
        if msg_type == "move":
            await self._handle_move(payload)
        elif msg_type == "restart":
            await self._handle_restart()
        elif msg_type == "ping":
            await self.send_json({"type": "pong"})
        else:
            await self.send_json({"type": "error", "message": f"未知消息类型: {msg_type}"})

    async def _handle_move(self, payload):
        try:
            x = int(payload.get("x"))
            y = int(payload.get("y"))
        except (TypeError, ValueError):
            await self.send_json({"type": "error", "message": "坐标格式错误。"})
            return

        error_message = None
        reason = None
        with self.rooms_lock:
            room = self.rooms.get(self.room_id)
            if not room:
                error_message = "房间不存在。"
            elif self.role != "player":
                error_message = "观战模式下不能落子。"
            elif not self._is_current_player(room):
                error_message = "你不是当前房间玩家。"
            elif room["status"] != "playing":
                error_message = "当前不是进行中的对局。"
            elif room["turn"] != self.player_color:
                error_message = "还没轮到你落子。"
            elif not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                error_message = "坐标超出棋盘范围。"
            elif room["board"][y][x] != 0:
                error_message = "该位置已有棋子。"
            else:
                stone_value = 1 if self.player_color == "black" else 2
                room["board"][y][x] = stone_value
                room["move_count"] += 1
                room["last_move"] = {"x": x, "y": y, "color": self.player_color}

                if self._check_winner(room["board"], x, y, stone_value):
                    room["status"] = "finished"
                    room["winner"] = self.player_color
                elif room["move_count"] >= BOARD_SIZE * BOARD_SIZE:
                    room["status"] = "finished"
                    room["winner"] = "draw"
                else:
                    room["turn"] = "white" if self.player_color == "black" else "black"

                reason = "move"

        if error_message:
            await self.send_json({"type": "error", "message": error_message})
            return

        if reason:
            await self._broadcast_room_state(reason=reason)

    async def _handle_restart(self):
        error_message = None
        should_restart = False
        with self.rooms_lock:
            room = self.rooms.get(self.room_id)
            if not room:
                error_message = "房间不存在。"
            elif self.role != "player":
                error_message = "仅玩家可重开对局。"
            elif not self._is_current_player(room):
                error_message = "仅玩家可重开对局。"
            elif not self._both_players_ready(room):
                error_message = "需要两位玩家都在房间中。"
            else:
                self._reset_board(room)
                room["status"] = "playing"
                should_restart = True

        if error_message:
            await self.send_json({"type": "error", "message": error_message})
            return

        if should_restart:
            await self._broadcast_room_state(reason="restart")

    async def _broadcast_room_state(self, reason):
        payload = self._build_room_payload(reason=reason)
        if not payload:
            return
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "room_state_message",
                "payload": payload,
            },
        )

    async def room_state_message(self, event):
        await self.send_json(event["payload"])

    def _build_room_payload(self, reason):
        with self.rooms_lock:
            room = self.rooms.get(self.room_id)
            if not room:
                return None

            spectators = [
                {"nickname": spectator["nickname"]}
                for spectator in room["spectators"].values()
            ]

            return {
                "type": "room_state",
                "roomId": self.room_id,
                "reason": reason,
                "status": room["status"],
                "turn": room["turn"],
                "winner": room["winner"],
                "board": [row[:] for row in room["board"]],
                "lastMove": dict(room["last_move"]) if room["last_move"] else None,
                "players": {
                    "black": self._public_player(room["players"]["black"]),
                    "white": self._public_player(room["players"]["white"]),
                },
                "spectators": spectators,
                "online": self._build_online_summary_locked(room),
            }

    @staticmethod
    def _public_player(player):
        if not player:
            return None
        return {"nickname": player["nickname"]}

    @staticmethod
    def _create_room():
        return {
            "players": {"black": None, "white": None},
            "spectators": {},
            "board": _create_empty_board(),
            "turn": "black",
            "status": "waiting",
            "winner": None,
            "move_count": 0,
            "last_move": None,
        }

    @staticmethod
    def _assign_player(room, channel_name, nickname):
        if room["players"]["black"] is None:
            room["players"]["black"] = {"channel_name": channel_name, "nickname": nickname}
            color = "black"
        elif room["players"]["white"] is None:
            room["players"]["white"] = {"channel_name": channel_name, "nickname": nickname}
            color = "white"
        else:
            return None

        if GomokuConsumer._both_players_ready(room):
            GomokuConsumer._reset_board(room)
            room["status"] = "playing"
        else:
            room["status"] = "waiting"
        return color

    @staticmethod
    def _remove_player(room, channel_name):
        removed = False
        for color in ("black", "white"):
            player = room["players"][color]
            if player and player["channel_name"] == channel_name:
                room["players"][color] = None
                removed = True
        return removed

    @staticmethod
    def _is_bound_player(room, player_color=None, channel_name=None):
        if player_color is None or channel_name is None:
            return False
        player = room["players"].get(player_color)
        return bool(player and player["channel_name"] == channel_name)

    def _is_current_player(self, room):
        return self._is_bound_player(room, self.player_color, self.channel_name)

    @staticmethod
    def _both_players_ready(room):
        return bool(room["players"]["black"] and room["players"]["white"])

    @staticmethod
    def _count_players(room):
        return int(room["players"]["black"] is not None) + int(room["players"]["white"] is not None)

    def _build_online_summary_locked(self, room):
        room_players = self._count_players(room)
        room_spectators = len(room["spectators"])
        active_rooms = 0
        for item in self.rooms.values():
            if self._count_players(item) > 0 or len(item["spectators"]) > 0:
                active_rooms += 1

        return {
            "room": {
                "players": room_players,
                "spectators": room_spectators,
                "total": room_players + room_spectators,
            },
            "global": {
                "totalConnections": len(self.active_connections),
                "rooms": active_rooms,
            },
        }

    @staticmethod
    def _reset_board(room):
        room["board"] = _create_empty_board()
        room["turn"] = "black"
        room["winner"] = None
        room["move_count"] = 0
        room["last_move"] = None

    @staticmethod
    def _check_winner(board, x, y, stone):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            count += GomokuConsumer._count_direction(board, x, y, dx, dy, stone)
            count += GomokuConsumer._count_direction(board, x, y, -dx, -dy, stone)
            if count >= 5:
                return True
        return False

    @staticmethod
    def _count_direction(board, x, y, dx, dy, stone):
        total = 0
        cx = x + dx
        cy = y + dy
        while 0 <= cx < BOARD_SIZE and 0 <= cy < BOARD_SIZE and board[cy][cx] == stone:
            total += 1
            cx += dx
            cy += dy
        return total
