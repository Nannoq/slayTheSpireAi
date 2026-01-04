import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.state import State


def main():
    data_dir = ROOT / "ressources" / "test_json"
    files = sorted(list(data_dir.glob("*.json")))
    if not files:
        print("No json files found in", data_dir)
        return 2

    lengths = {}
    for p in files:
        with open(p, "r", encoding="utf-8") as fh:
            j = json.load(fh)
        s = State(j)
        vec = s.encode_state()
        lengths[p.name] = len(vec)

    # print results
    for name, l in lengths.items():
        print(f"{name}: {l}")

    vals = set(lengths.values())
    if len(vals) == 1:
        size = vals.pop()
        print("OK — all vectors have the same length:", size)
        # also compare with State.get_size()
        print("State.get_size():", State.get_size())
        if State.get_size() == size:
            print("State.get_size() matches encoded vectors")
            return 0
        else:
            print("Mismatch: State.get_size() != encoded vector length")
            return 2
    else:
        print("ERROR — inconsistent vector lengths:")
        for name, l in lengths.items():
            print(f" - {name}: {l}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
