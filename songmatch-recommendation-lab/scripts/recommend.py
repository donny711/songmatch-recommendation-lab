"""Run the engine before the interface: python -m scripts.recommend."""
import argparse
import json
from dataclasses import asdict
from src.data import load_catalog, dataset_version, catalog_for_scope
from src.recommend import Recommender, ALGORITHM_VERSION

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--songs", nargs="+", help="3–5 catalog song IDs; defaults to three songs in the selected library")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--library",choices=["popular","all"],default="popular")
    args = parser.parse_args()
    engine = Recommender(catalog_for_scope(load_catalog(),args.library))
    selected = args.songs or engine.ids[:3]
    print(json.dumps({"dataset_version": dataset_version(scope=args.library), "algorithm_version": ALGORITHM_VERSION,
                      "seed": args.seed, "selected": selected,
                      "results": {k: asdict(v) for k,v in engine.compare(selected,args.seed).items()}}, indent=2))

if __name__ == "__main__":
    main()
