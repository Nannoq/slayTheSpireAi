import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.state import State
f = ROOT / "ressources" / "test_json" / "fight.json"
with open(f, "r", encoding="utf-8") as fh:
    j = json.load(fh)

s = State(j)
vec = s.encode_state()
print(len(vec))
print(vec.shape)
