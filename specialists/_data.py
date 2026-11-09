"""Shared data access for the specialists. Loads the consortium once; each member's rows stay in its own list."""
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config  # noqa: E402
from fl.consortium import load_world  # noqa: E402


@lru_cache(maxsize=1)
def world():
    return load_world(config.CONSORTIUM)


def member(name):
    return world().member(name)


def record(member_name, record_id):
    c = member(member_name)
    for r in c.rows:
        if r[world().schema["id_column"]] == record_id:
            return r
    return None


def label():
    return world().label


def features():
    return world().features
