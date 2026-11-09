"""
THE CONSORTIUM LOADER: builds a World from data/consortia/<name>/.

One member per CSV. Features are standardized with the reference means and sds
in schema.json (agreed in advance by the consortium, so nobody shares raw
statistics). The coordinator's neutral_eval.csv becomes the test set, tagged
by the member population each row came from, so accuracy is reported per member.

    from fl.consortium import load_world
    world = load_world("hospitals")
    world.clients[0].name, world.clients[0].X_train.shape
    world.describe()
"""
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "consortia"


@dataclass
class Client:
    name: str
    X_train: np.ndarray
    y_train: np.ndarray
    ids: list = field(default_factory=list)
    rows: list = field(default_factory=list)       # the raw records (human units), for the specialists

    @property
    def n(self):
        return len(self.y_train)

    def describe(self):
        return f"{self.name:<28} n={self.n:<6} rate {self.y_train.mean():.2f}"


@dataclass
class World:
    name: str
    title: str
    unit: str
    label: str
    features: list
    segments: list
    schema: dict
    clients: list
    X_test: np.ndarray
    y_test: np.ndarray
    test_source: np.ndarray
    skew: str = "provided"

    def test_for(self, k):
        m = self.test_source == k
        return self.X_test[m], self.y_test[m]

    def member(self, name):
        for c in self.clients:
            if c.name == name:
                return c
        raise KeyError(f"no member named {name}; members are {[c.name for c in self.clients]}")

    def describe(self):
        lines = [f"Consortium: {self.title}  ({len(self.clients)} members, outcome {self.label})"]
        lines += ["  " + c.describe() for c in self.clients]
        lines.append(f"  {'neutral eval':<28} n={len(self.y_test):<6} rate {self.y_test.mean():.2f}   ({self.schema['eval_per_member']} rows from each member's population)")
        return "\n".join(lines)


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def standardize(rows, schema):
    mu = np.array([f["mean"] for f in schema["features"]], dtype=float)
    sd = np.array([f["sd"] for f in schema["features"]], dtype=float)
    X = np.array([[float(r[f["name"]]) for f in schema["features"]] for r in rows], dtype=float)
    return (X - mu) / sd


def load_schema(name):
    with open(DATA / name / "schema.json") as f:
        return json.load(f)


def load_world(name):
    folder = DATA / name
    if not folder.exists():
        raise SystemExit(f"no consortium folder {folder}; choices: {sorted(p.name for p in DATA.iterdir() if p.is_dir())}")
    schema = load_schema(name)
    label = schema["label"]
    clients = []
    for m in schema["members"]:
        rows = read_csv(folder / m["file"])
        X = standardize(rows, schema)
        y = np.array([int(r[label]) for r in rows])
        clients.append(Client(m["name"], X, y, ids=[r[schema["id_column"]] for r in rows], rows=rows))
    ev = read_csv(folder / schema["neutral_eval"])
    X_test = standardize(ev, schema)
    y_test = np.array([int(r[label]) for r in ev])
    names = [c.name for c in clients]
    test_source = np.array([names.index(r["source_member"]) for r in ev])
    # attacks need the feature order and a trigger pattern (two rarely-coincident feature values)
    from fl import attacks
    attacks.FEATURES = [f["name"] for f in schema["features"]]
    cont = [f for f in schema["features"] if f.get("type") != "binary"]
    attacks.TRIGGER = {f["name"]: 2.5 for f in cont[:2]}
    return World(name, schema["title"], schema["unit"], label, [f["name"] for f in schema["features"]], schema["segments"], schema,
                 clients, X_test, y_test, test_source)


def pooled(world):
    """The forbidden ideal: every member's rows in one table. Baseline only; never ship this."""
    return np.vstack([c.X_train for c in world.clients]), np.concatenate([c.y_train for c in world.clients])
