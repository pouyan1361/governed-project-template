import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config
from fl.consortium import load_world


def test_world_loads_and_members_match_schema():
    w = load_world(config.CONSORTIUM)
    assert len(w.clients) == len(w.schema["members"])
    assert w.X_test.shape[1] == len(w.features)
    assert all(c.X_train.shape[1] == len(w.features) for c in w.clients)


def test_standardization_is_about_zero_mean_for_reference_member():
    w = load_world(config.CONSORTIUM)
    big = max(w.clients, key=lambda c: c.n)
    assert abs(float(big.X_train.mean())) < 0.6


def test_test_set_tagged_per_member():
    w = load_world(config.CONSORTIUM)
    for k in range(len(w.clients)):
        Xk, yk = w.test_for(k)
        assert len(yk) == w.schema["eval_per_member"]
