from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

# encoding constants (match those in game_env.py)
MAX_HAND = 10
MAX_DECK = 50
MAX_MONSTERS = 6
MAX_SHOP_CARDS = 7
MAX_SHOP_POTIONS = 3
MAX_SHOP_RELICS = 3
MAX_MAP_NODES = 70
CARD_FEATURES = 13
CARD_TYPE_MAP = {"ATTACK": 0, "SKILL": 1, "POWER": 2}
ROOM_TYPE_MAP = {"MonsterRoom":0, "ShopRoom":1, "EventRoom":2, "RestRoom":3}
RARITY_MAP = {"BASIC": 0, "COMMON": 1, "UNCOMMON": 2, "RARE": 3, "SPECIAL": 4, "CURSE": 5}
# room phases mapping for one-hot encoding
ROOM_PHASES = ["COMBAT", "COMPLETE", "EVENT", "SHOP", "REST", "UNKNOWN"]
ROOM_PHASE_MAP = {v: i for i, v in enumerate(ROOM_PHASES)}
MAP_SYMBOLS = ["M", "?", "$", "E", "R"]
MAP_SYMBOL_INDEX = {s: i for i, s in enumerate(MAP_SYMBOLS)}

# additional encoding limits
MAX_OWNED_RELICS = 10
MAX_PLAYER_POWERS = 6
MAX_PLAYER_POTIONS = 3
MAX_PILE_TOP = 3

@dataclass
class Monster:
    current_hp: int = 0
    max_hp: int = 0
    block: int = 0
    move_base_damage: int = 0
    intent: Optional[str] = None
    buffs: int = 0
    debuffs: int = 0
    is_gone: bool = False
    half_dead: bool = False
    move_hits: int = 0

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Monster":
        return Monster(
            current_hp=data.get("current_hp", 0),
            max_hp=data.get("max_hp", 0),
            block=data.get("block", 0),
            move_base_damage=data.get("move_base_damage", 0),
            intent=data.get("intent") or data.get("intent_name"),
            buffs=len(data.get("buffs", [])) if data.get("buffs") is not None else 0,
            debuffs=len(data.get("debuffs", [])) if data.get("debuffs") is not None else 0,
            is_gone=bool(data.get("is_gone", False)),
            half_dead=bool(data.get("half_dead", False)),
            move_hits=data.get("move_hits", 0),
        )

    def update_from_json(self, data: Dict[str, Any]) -> None:
        # Replace all fields; defaults used when keys missing
        self.current_hp = data.get("current_hp", 0)
        self.max_hp = data.get("max_hp", 0)
        self.block = data.get("block", 0)
        self.move_base_damage = data.get("move_base_damage", 0)
        self.intent = data.get("intent") or data.get("intent_name")
        self.buffs = len(data.get("buffs", [])) if data.get("buffs") is not None else 0
        self.debuffs = len(data.get("debuffs", [])) if data.get("debuffs") is not None else 0
        self.is_gone = bool(data.get("is_gone", False))
        self.half_dead = bool(data.get("half_dead", False))
        self.move_hits = data.get("move_hits", 0)

    def encode(self) -> List[float]:
        intent_flag = 1.0 if self.intent else 0.0
        return [self.current_hp or 0, self.max_hp or 0, self.block or 0, self.move_base_damage or 0, intent_flag, float(self.buffs or 0), float(self.debuffs or 0), 1.0 if self.is_gone else 0.0, 1.0 if self.half_dead else 0.0, float(self.move_hits or 0)]

    @staticmethod
    def encode_size() -> int:
        return 10
    
    # renamed getter for size
    @staticmethod
    def get_size() -> int:
        return Monster.encode_size()


@dataclass
class CombatState:
    monsters: List[Monster] = field(default_factory=list)

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "CombatState":
        monsters = [Monster.from_json(m) for m in data.get("monsters", [])]
        return CombatState(monsters=monsters)

    def update_from_json(self, data: Dict[str, Any]) -> None:
        # Replace monsters list entirely (empty list if absent)
        self.monsters = [Monster.from_json(m) for m in data.get("monsters", [])]

    def encode(self) -> List[float]:
        vec: List[float] = []
        for i in range(MAX_MONSTERS):
            if i < len(self.monsters):
                vec.extend(self.monsters[i].encode())
            else:
                vec.extend([0.0] * Monster.encode_size())
        return vec

    @staticmethod
    def encode_size() -> int:
        return MAX_MONSTERS * Monster.encode_size()

    @staticmethod
    def get_size() -> int:
        return CombatState.encode_size()


@dataclass
class Player:
    current_hp: int = 0
    max_hp: int = 0
    energy: int = 0
    block: int = 0
    powers_count: int = 0

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Player":
        return Player(
            current_hp=data.get("current_hp", 0),
            max_hp=data.get("max_hp", 0),
            energy=data.get("energy", 0),
            block=data.get("block", 0) or data.get("current_block", 0) if data is not None else 0,
            powers_count=len(data.get("powers", [])) if data.get("powers") is not None else 0,
        )

    def update_from_json(self, data: Dict[str, Any]) -> None:
        # Replace all fields; defaults used when keys missing
        self.current_hp = data.get("current_hp", 0)
        self.max_hp = data.get("max_hp", 0)
        self.energy = data.get("energy", 0)
        self.block = data.get("block", 0) or data.get("current_block", 0) if data is not None else 0
        self.powers_count = len(data.get("powers", [])) if data.get("powers") is not None else 0

    def encode(self) -> List[float]:
        return [self.current_hp or 0, self.max_hp or 0, self.energy or 0, self.block or 0, float(self.powers_count or 0)]

    @staticmethod
    def encode_size() -> int:
        return 5

    @staticmethod
    def get_size() -> int:
        return Player.encode_size()


@dataclass
class ShopCard:
    price: int = 0
    cost: int = 0
    type: str = "SKILL"
    upgrades: int = 0
    has_target: bool = False
    exhausts: bool = False
    id: Optional[str] = None
    uuid: Optional[str] = None
    rarity: Optional[str] = None
    ethereal: bool = False
    is_playable: bool = False

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "ShopCard":
        return ShopCard(
            price=data.get("price", 0),
            cost=data.get("cost", 0),
            type=data.get("type", "SKILL"),
            upgrades=data.get("upgrades", 0),
            has_target=data.get("has_target", False),
            exhausts=data.get("exhausts", False),
            id=data.get("id") or data.get("name"),
            uuid=data.get("uuid") or data.get("uuid"),
            rarity=data.get("rarity"),
            ethereal=bool(data.get("ethereal", False)),
            is_playable=bool(data.get("is_playable", False)),
        )

    def update_from_json(self, data: Dict[str, Any]) -> None:
        self.price = data.get("price", 0)
        self.cost = data.get("cost", 0) if "cost" in data else self.cost
        self.type = data.get("type", "SKILL") if "type" in data else self.type
        self.upgrades = data.get("upgrades", 0) if "upgrades" in data else self.upgrades
        self.has_target = bool(data.get("has_target", False)) if "has_target" in data else self.has_target
        self.exhausts = bool(data.get("exhausts", False)) if "exhausts" in data else self.exhausts
        self.id = data.get("id") or data.get("name") if ("id" in data or "name" in data) else self.id
        self.uuid = data.get("uuid") if "uuid" in data else self.uuid
        self.rarity = data.get("rarity") if "rarity" in data else self.rarity
        self.ethereal = bool(data.get("ethereal", False)) if "ethereal" in data else self.ethereal
        self.is_playable = bool(data.get("is_playable", False)) if "is_playable" in data else self.is_playable

    def encode(self) -> List[float]:
        rarity_idx = RARITY_MAP.get(self.rarity, 0) if self.rarity is not None else 0
        return [
            self.price or 0,
            self.cost or 0,
            CARD_TYPE_MAP.get(self.type, 1),
            float(self.upgrades or 0),
            1.0 if self.has_target else 0.0,
            1.0 if self.exhausts else 0.0,
            float(rarity_idx),
            1.0 if self.ethereal else 0.0,
            1.0 if self.is_playable else 0.0,
            1.0 if self.id else 0.0,
            1.0 if self.uuid else 0.0,
        ]

    @staticmethod
    def encode_size() -> int:
        return 11

    @staticmethod
    def get_size() -> int:
        return ShopCard.encode_size()


@dataclass
class Potion:
    price: int = 0
    id: Optional[str] = None

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Potion":
        return Potion(price=data.get("price", 0), id=data.get("id") or data.get("name"))

    def update_from_json(self, data: Dict[str, Any]) -> None:
        self.price = data.get("price", 0)

    def encode(self) -> List[float]:
        return [self.price or 0, 1.0 if self.id else 0.0]

    @staticmethod
    def encode_size() -> int:
        return 2

    @staticmethod
    def get_size() -> int:
        return Potion.encode_size()


@dataclass
class Relic:
    price: int = 0
    id: Optional[str] = None

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "Relic":
        return Relic(price=data.get("price", 0), id=data.get("id") or data.get("name"))

    def update_from_json(self, data: Dict[str, Any]) -> None:
        self.price = data.get("price", 0) if "price" in data else self.price
        self.id = data.get("id") or data.get("name") if ("id" in data or "name" in data) else self.id

    def encode(self) -> List[float]:
        return [self.price or 0, 1.0 if self.id else 0.0]

    @staticmethod
    def encode_size() -> int:
        return 2

    @staticmethod
    def get_size() -> int:
        return Relic.encode_size()


@dataclass
class ScreenState:
    cards: List[ShopCard] = field(default_factory=list)
    potions: List[Potion] = field(default_factory=list)
    relics: List[Relic] = field(default_factory=list)
    purge_available: bool = False
    purge_cost: int = 0
    # event specific
    event_id: Optional[str] = None
    event_name: Optional[str] = None
    body_text: Optional[str] = None
    options: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "ScreenState":
        cards = [ShopCard.from_json(c) for c in data.get("cards", [])]
        potions = [Potion.from_json(p) for p in data.get("potions", [])]
        relics = [Relic.from_json(r) for r in data.get("relics", [])]
        return ScreenState(
            cards=cards,
            potions=potions,
            relics=relics,
            purge_available=data.get("purge_available", False),
            purge_cost=data.get("purge_cost", 0),
            event_id=data.get("event_id"),
            event_name=data.get("event_name"),
            body_text=data.get("body_text"),
            options=data.get("options", []),
        )

    def update_from_json(self, data: Dict[str, Any]) -> None:
        # Replace all fields; defaults used when keys missing
        self.cards = [ShopCard.from_json(c) for c in data.get("cards", [])]
        self.potions = [Potion.from_json(p) for p in data.get("potions", [])]
        self.relics = [Relic.from_json(r) for r in data.get("relics", [])]
        self.purge_available = bool(data.get("purge_available", False))
        self.purge_cost = data.get("purge_cost", 0)
        # event fields
        self.event_id = data.get("event_id")
        self.event_name = data.get("event_name")
        self.body_text = data.get("body_text")
        self.options = data.get("options", [])

    def encode(self, room_type: Optional[str] = None, raw_relics: Optional[List[Dict[str, Any]]] = None) -> List[float]:
        # Encode shop cards, potions, relics and purge info.
        vec: List[float] = []
        if room_type == "ShopRoom":
            cards = self.cards
            potions = self.potions
            relics = self.relics
        else:
            cards = []
            potions = []
            relics = raw_relics or []

        for i in range(MAX_SHOP_CARDS):
            if i < len(cards):
                # cards may be ShopCard or raw dict
                if hasattr(cards[i], "encode"):
                    vec.extend(cards[i].encode())
                else:
                    # raw dict - attempt same fields
                    vec.extend([
                        cards[i].get("price", 0),
                        cards[i].get("cost", 0),
                        CARD_TYPE_MAP.get(cards[i].get("type", "SKILL"), 1),
                        float(cards[i].get("upgrades", 0)),
                        1.0 if cards[i].get("has_target", False) else 0.0,
                        1.0 if cards[i].get("exhausts", False) else 0.0,
                    ])
            else:
                vec.extend([0] * ShopCard.encode_size())

        for i in range(MAX_SHOP_POTIONS):
            if i < len(potions):
                if hasattr(potions[i], "encode"):
                    vec.extend(potions[i].encode())
                else:
                    vec.extend([potions[i].get("price", 0), 1.0 if (potions[i].get("id") or potions[i].get("name")) else 0.0])
            else:
                vec.extend([0] * Potion.encode_size())

        for i in range(MAX_SHOP_RELICS):
            if i < len(relics):
                r = relics[i]
                if hasattr(r, "encode"):
                    vec.extend(r.encode())
                else:
                    vec.extend([r.get("price", 0), 1.0 if (r.get("id") or r.get("name")) else 0.0])
            else:
                vec.extend([0] * Relic.encode_size())

        vec.append(1 if self.purge_available else 0)
        vec.append(self.purge_cost or 0)
        vec.append(1.0 if (self.event_id or self.event_name) else 0.0)
        vec.append(float(len(self.options or [])))
        return vec

    @staticmethod
    def encode_size() -> int:
        # shop cards: ShopCard.encode_size() each, potions: Potion.encode_size(), relics: Relic.encode_size(), purge(2), event(2)
        return MAX_SHOP_CARDS * ShopCard.encode_size() + MAX_SHOP_POTIONS * Potion.encode_size() + MAX_SHOP_RELICS * Relic.encode_size() + 2 + 2

    @staticmethod
    def get_size() -> int:
        return ScreenState.encode_size()


@dataclass
class MapNode:
    symbol: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    children: List[Dict[str, Any]] = field(default_factory=list)
    parents: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "MapNode":
        return MapNode(
            symbol=data.get("symbol"),
            x=data.get("x"),
            y=data.get("y"),
            children=data.get("children", []),
            parents=data.get("parents", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "x": self.x,
            "y": self.y,
            "children": self.children,
            "parents": self.parents,
        }


@dataclass
class Map:
    nodes: List[MapNode] = field(default_factory=list)

    @staticmethod
    def from_json(data: List[Dict[str, Any]]) -> "Map":
        nodes = [MapNode.from_json(n) for n in (data or [])][:MAX_MAP_NODES]
        return Map(nodes=nodes)

    def update_from_json(self, data: List[Dict[str, Any]]) -> None:
        # full replace semantics: limit to MAX_MAP_NODES
        self.nodes = [MapNode.from_json(n) for n in (data or [])][:MAX_MAP_NODES]

    def to_list(self) -> List[Dict[str, Any]]:
        return [n.to_dict() for n in self.nodes]

    def encode(self) -> List[float]:
        # encoding: number of nodes, cap flag, and histogram of known symbols
        counts = [0] * len(MAP_SYMBOLS)
        for n in self.nodes:
            s = (n.symbol or "")
            idx = MAP_SYMBOL_INDEX.get(s)
            if idx is not None:
                counts[idx] += 1
        cap_flag = 1.0 if len(self.nodes) >= MAX_MAP_NODES else 0.0
        return [float(len(self.nodes)), cap_flag] + [float(c) for c in counts]

    @staticmethod
    def encode_size() -> int:
        return 2 + len(MAP_SYMBOLS)


@dataclass
class GameState:
    floor: Optional[int] = None
    act: Optional[int] = None
    room_phase: Optional[str] = None
    screen_name: Optional[str] = None
    room_type: Optional[str] = None
    gold: int = 0
    map: Map = field(default_factory=Map)
    player: Player = field(default_factory=Player)
    combat_state: CombatState = field(default_factory=CombatState)
    screen_state: ScreenState = field(default_factory=ScreenState)

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "GameState":
        return GameState(
            floor=data.get("floor"),
            act=data.get("act"),
            room_phase=data.get("room_phase"),
            screen_name=data.get("screen_name"),
            room_type=data.get("room_type"),
            gold=data.get("gold", 0),
            map=Map.from_json(data.get("map", [])),
            player=Player.from_json(data.get("player", {})),
            combat_state=CombatState.from_json(data.get("combat_state", {})),
            screen_state=ScreenState.from_json(data.get("screen_state", {})),
        )

    def encode(self, raw_gs: Dict[str, Any]) -> List[float]:
        # Player + gold
        player_vec = self.player.encode() if self.player is not None else [0,0,0]
        gold = self.gold or 0
        player_vec_with_gold = player_vec + [gold]

        # Combat
        combat_vec = self.combat_state.encode() if self.combat_state is not None else [0] * CombatState.encode_size()

        # Screen state: pass room_type and raw relics if needed
        room_type = self.room_type or raw_gs.get("room_type")
        raw_relics = raw_gs.get("relics", [])
        screen_vec = self.screen_state.encode(room_type=room_type, raw_relics=raw_relics)

        # map summary
        map_vec = self.map.encode() if self.map is not None else [0.0] * Map.encode_size()

        # combat piles counts (draw/discard/exhaust) if present in raw_gs.combat_state
        cs = raw_gs.get("combat_state", {}) or {}
        draw_count = float(len(cs.get("draw_pile", []))) if cs is not None else 0.0
        discard_count = float(len(cs.get("discard_pile", []))) if cs is not None else 0.0
        exhaust_count = float(len(cs.get("exhaust_pile", []))) if cs is not None else 0.0

        pile_vec = [draw_count, discard_count, exhaust_count]

        return player_vec_with_gold + map_vec + pile_vec + combat_vec + screen_vec

    @staticmethod
    def encode_size() -> int:
        # player (3) + gold (1) + map summary + 3 pile counts + combat + screen
        return Player.encode_size() + 1 + Map.encode_size() + 3 + CombatState.encode_size() + ScreenState.encode_size()

    @staticmethod
    def get_size() -> int:
        return GameState.encode_size()

    def update_from_json(self, data: Dict[str, Any]) -> None:
        # Replace all fields; defaults used when keys missing
        self.floor = data.get("floor")
        self.act = data.get("act")
        self.room_phase = data.get("room_phase")
        self.screen_name = data.get("screen_name")
        self.room_type = data.get("room_type")
        self.gold = data.get("gold", 0)
        self.map = Map.from_json(data.get("map", []))

        self.player = Player.from_json(data.get("player", {}))
        self.combat_state = CombatState.from_json(data.get("combat_state", {}))
        self.screen_state = ScreenState.from_json(data.get("screen_state", {}))


@dataclass
class State:
    raw_json: Dict[str, Any] = field(default_factory=dict)
    game_state: GameState = field(default_factory=GameState)
    available_commands: List[str] = field(default_factory=list)
    in_game: bool = False
    ready_for_command: bool = True

    def __init__(self, json_data: Dict[str, Any]):
        # initialize attributes with defaults before updating
        self.raw_json = {}
        self.game_state = GameState()
        self.available_commands = []
        self.in_game = False
        self.ready_for_command = True
        self.update_from_json(json_data)

    def update_from_json(self, json_data: Dict[str, Any]) -> None:
        # Replace entire state: if a field is not present in the incoming
        # JSON we reset it to its default value to avoid leaking stale data.
        self.raw_json = json_data or {}

        # game_state: fully replace if present, otherwise reset to default
        if "game_state" in self.raw_json:
            gs = self.raw_json.get("game_state") or {}
            self.game_state = GameState.from_json(gs)
        else:
            self.game_state = GameState()

        # available_commands: replace or reset to empty
        if "available_commands" in self.raw_json:
            self.available_commands = self.raw_json.get("available_commands", [])
        else:
            self.available_commands = []

        # booleans: replace or reset to defaults
        if "in_game" in self.raw_json:
            self.in_game = bool(self.raw_json.get("in_game", False))
        else:
            self.in_game = False

        if "ready_for_command" in self.raw_json:
            self.ready_for_command = bool(self.raw_json.get("ready_for_command", True))
        else:
            self.ready_for_command = True

    def _encode_card_features(self, card: Any) -> List[float]:
        # produce exactly CARD_FEATURES floats for a card-like dict/object
        if card is None:
            return [0.0] * CARD_FEATURES
        if isinstance(card, dict):
            cost = card.get("cost", 0) or 0
            damage = card.get("damage", 0) or card.get("base_damage", 0) or 0
            block = card.get("block", 0) or 0
            type_idx = CARD_TYPE_MAP.get(card.get("type", "SKILL"), 1)
            misc = card.get("magic", 0) or 0
            upgrades = card.get("upgrades", 0) or 0
            has_target = 1.0 if card.get("has_target", False) else 0.0
            exhausts = 1.0 if card.get("exhausts", False) else 0.0
            rarity_idx = RARITY_MAP.get(card.get("rarity"), 0) if card.get("rarity") is not None else 0
            ethereal = 1.0 if card.get("ethereal", False) else 0.0
            is_playable = 1.0 if card.get("is_playable", False) else 0.0
            id_present = 1.0 if (card.get("id") or card.get("name")) else 0.0
            uuid_present = 1.0 if card.get("uuid") else 0.0
        else:
            cost = getattr(card, "cost", 0) or 0
            damage = getattr(card, "damage", 0) or getattr(card, "base_damage", 0) or 0
            block = getattr(card, "block", 0) or 0
            type_idx = CARD_TYPE_MAP.get(getattr(card, "type", "SKILL"), 1)
            misc = getattr(card, "magic", 0) or 0
            upgrades = getattr(card, "upgrades", 0) or 0
            has_target = 1.0 if getattr(card, "has_target", False) else 0.0
            exhausts = 1.0 if getattr(card, "exhausts", False) else 0.0
            rarity_idx = RARITY_MAP.get(getattr(card, "rarity", None), 0) if getattr(card, "rarity", None) is not None else 0
            ethereal = 1.0 if getattr(card, "ethereal", False) else 0.0
            is_playable = 1.0 if getattr(card, "is_playable", False) else 0.0
            id_present = 1.0 if (getattr(card, "id", None) or getattr(card, "name", None)) else 0.0
            uuid_present = 1.0 if getattr(card, "uuid", None) else 0.0
        return [
            float(cost), float(damage), float(block), float(type_idx), float(misc), float(upgrades), float(has_target), float(exhausts), float(rarity_idx), float(ethereal), float(is_playable), float(id_present), float(uuid_present)
        ]

    @staticmethod
    def encode_size() -> int:
        # total full vector size: room one-hot (4) + game_state (player+gold + combat + screen)
        # plus hand and deck fixed-size encodings
        game_state_part = GameState.encode_size()
        hand_part = MAX_HAND * CARD_FEATURES
        deck_part = MAX_DECK * CARD_FEATURES
        room_part = 4
        # room_phase one-hot + floor + act
        extra_top = len(ROOM_PHASES) + 2
        # additional blocks we add at State level:
        # ascension (1) + class one-hot + player potions + owned relics + player powers + top of piles
        ascension_part = 1
        player_potions_part = MAX_PLAYER_POTIONS * 4  # id_present, can_use, can_discard, requires_target
        owned_relics_part = MAX_OWNED_RELICS * 2  # id_present, counter
        player_powers_part = MAX_PLAYER_POWERS * 2  # id_present, amount
        # per-pile summary features: rarities + types + avg_cost + avg_upgrades + id_count
        per_pile_features = len(RARITY_MAP) + len(CARD_TYPE_MAP) + 3
        top_piles_part = 3 * per_pile_features
        extra_blocks = ascension_part + player_potions_part + owned_relics_part + player_powers_part + top_piles_part
        return room_part + extra_top + game_state_part + extra_blocks + hand_part + deck_part

    @staticmethod
    def get_size() -> int:
        return State.encode_size()

    def encode_state(self) -> np.ndarray:
        raw_gs = (self.raw_json.get("game_state") or {})

        # room one-hot
        room_type = self.game_state.room_type or raw_gs.get("room_type", "UnknownRoom")
        room_vector = [0] * 4
        room_vector[ROOM_TYPE_MAP.get(room_type, 0)] = 1

        # room phase one-hot + floor/act
        phase = self.game_state.room_phase or raw_gs.get("room_phase", "UNKNOWN")
        phase_vector = [0] * len(ROOM_PHASES)
        phase_vector[ROOM_PHASE_MAP.get(phase, ROOM_PHASE_MAP["UNKNOWN"])] = 1
        floor = float(self.game_state.floor if self.game_state.floor is not None else raw_gs.get("floor", 0) or 0)
        act = float(self.game_state.act if self.game_state.act is not None else raw_gs.get("act", 0) or 0)

        game_vec = self.game_state.encode(raw_gs)
        # game_vec = [player_current_hp, player_max_hp, player_energy, gold, ...combat..., ...screen...]
        player_part = game_vec[:4]
        rest_part = game_vec[4:]

        # hand
        hand = raw_gs.get("hand", [])
        hand_vector: List[float] = []
        for i in range(MAX_HAND):
            if i < len(hand):
                hand_vector.extend(self._encode_card_features(hand[i]))
            else:
                hand_vector.extend([0] * CARD_FEATURES)

        # deck
        deck = raw_gs.get("deck", [])
        deck_vector: List[float] = []
        for i in range(MAX_DECK):
            if i < len(deck):
                deck_vector.extend(self._encode_card_features(deck[i]))
            else:
                deck_vector.extend([0] * CARD_FEATURES)

        # --- additional blocks: ascension + class + player potions + owned relics + player powers + top of piles
        # ascension
        ascension = float(raw_gs.get("ascension_level", 0) or 0)

        # player potions (detailed)
        player_potions_vec: List[float] = []
        potions_owned = raw_gs.get("potions", []) or []
        for i in range(MAX_PLAYER_POTIONS):
            if i < len(potions_owned):
                p = potions_owned[i]
                player_potions_vec.extend([
                    1.0 if (p.get("id") or p.get("name")) else 0.0,
                    1.0 if p.get("can_use", False) else 0.0,
                    1.0 if p.get("can_discard", False) else 0.0,
                    1.0 if p.get("requires_target", False) else 0.0,
                ])
            else:
                player_potions_vec.extend([0.0, 0.0, 0.0, 0.0])

        # owned relics (id presence + counter)
        relics_owned_vec: List[float] = []
        relics_owned = raw_gs.get("relics", []) or []
        for i in range(MAX_OWNED_RELICS):
            if i < len(relics_owned):
                r = relics_owned[i]
                relics_owned_vec.extend([
                    1.0 if (r.get("id") or r.get("name")) else 0.0,
                    float(r.get("counter", 0) or 0),
                ])
            else:
                relics_owned_vec.extend([0.0, 0.0])

        # player powers (presence + amount)
        player_powers_vec: List[float] = []
        player_obj = raw_gs.get("player", {}) or {}
        pows = player_obj.get("powers", []) or []
        for i in range(MAX_PLAYER_POWERS):
            if i < len(pows):
                pw = pows[i]
                player_powers_vec.extend([
                    1.0 if (pw.get("id") or pw.get("name")) else 0.0,
                    float(pw.get("amount", 0) or 0),
                ])
            else:
                player_powers_vec.extend([0.0, 0.0])

        # per-pile summary (draw/discard/exhaust):
        # - counts per rarity (len(RARITY_MAP))
        # - counts per type (len(CARD_TYPE_MAP))
        # - avg_cost, avg_upgrades, id_present_count
        top_piles_vec: List[float] = []
        cs = raw_gs.get("combat_state", {}) or {}
        for pile_name in ("draw_pile", "discard_pile", "exhaust_pile"):
            pile = cs.get(pile_name, []) or []
            rarity_counts = [0] * len(RARITY_MAP)
            type_counts = [0] * len(CARD_TYPE_MAP)
            total_cost = 0.0
            total_upgrades = 0.0
            id_count = 0
            for card in pile:
                if isinstance(card, dict):
                    r = card.get("rarity")
                    if r is not None:
                        idx = RARITY_MAP.get(r)
                        if idx is not None:
                            rarity_counts[idx] += 1
                    t = card.get("type", "SKILL")
                    type_counts[CARD_TYPE_MAP.get(t, 1)] += 1
                    total_cost += float(card.get("cost", 0) or 0)
                    total_upgrades += float(card.get("upgrades", 0) or 0)
                    if (card.get("id") or card.get("name")):
                        id_count += 1
                else:
                    # object-like card
                    r = getattr(card, "rarity", None)
                    if r is not None:
                        idx = RARITY_MAP.get(r)
                        if idx is not None:
                            rarity_counts[idx] += 1
                    t = getattr(card, "type", "SKILL")
                    type_counts[CARD_TYPE_MAP.get(t, 1)] += 1
                    total_cost += float(getattr(card, "cost", 0) or 0)
                    total_upgrades += float(getattr(card, "upgrades", 0) or 0)
                    if (getattr(card, "id", None) or getattr(card, "name", None)):
                        id_count += 1
            n = float(len(pile)) if len(pile) > 0 else 0.0
            avg_cost = (total_cost / n) if n > 0.0 else 0.0
            avg_upg = (total_upgrades / n) if n > 0.0 else 0.0
            # append counts (as floats), then averages and id_count
            top_piles_vec.extend([float(c) for c in rarity_counts])
            top_piles_vec.extend([float(c) for c in type_counts])
            top_piles_vec.append(avg_cost)
            top_piles_vec.append(avg_upg)
            top_piles_vec.append(float(id_count))

        full = np.array(
            room_vector + phase_vector + [floor, act] + player_part + [ascension] + player_potions_vec + relics_owned_vec + player_powers_vec + hand_vector + deck_vector + top_piles_vec + rest_part,
            dtype=np.float32,
        )
        return full
