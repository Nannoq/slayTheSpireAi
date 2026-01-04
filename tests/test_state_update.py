import json
import os
import sys
from pathlib import Path

# ensure src/ is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from state import State


DATA_DIR = ROOT / "ressources" / "test_json"


def load(name: str):
    p = DATA_DIR / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def show_state(s: State, label: str):
    gs = s.game_state
    print(f"== {label} ==")
    print(f"floor: {gs.floor}")
    print(f"act: {gs.act}")
    print(f"gold: {gs.gold}")
    print(f"screen_name: {gs.screen_name}")
    print(f"room_phase: {gs.room_phase}")
    print(f"player.current_hp: {gs.player.current_hp}")
    print(f"# monsters: {len(gs.combat_state.monsters)}")
    print(f"# shop cards: {len(gs.screen_state.cards)}")
    if gs.screen_state.event_name or gs.screen_state.event_id:
        print(f"event_name: {gs.screen_state.event_name}")
        print(f"event_id: {gs.screen_state.event_id}")
        print(f"# options: {len(gs.screen_state.options)}")
    print()


def main():
    # Load a full fight state
    fight = load("fight.json")
    s = State(fight)
    show_state(s, "Initial from fight.json")

    # Partial update: apply fight_reward (should update screen_name/room_phase/rewards but keep missing fields)
    fight_reward = load("fight_reward.json")
    s.update_from_json(fight_reward)
    show_state(s, "After update with fight_reward.json")

    # Partial update: apply shop state (will update screen_state.cards, purge info, gold if present)
    shop = load("shop.json")
    s.update_from_json(shop)
    show_state(s, "After update with shop.json")

    # Partial update: apply event state
    event = load("event.json")
    s.update_from_json(event)
    show_state(s, "After update with event.json")


if __name__ == "__main__":
    main()
