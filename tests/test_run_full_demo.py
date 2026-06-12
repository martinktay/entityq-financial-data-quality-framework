from __future__ import annotations

from entityq import run_full_demo


def test_run_full_demo_is_importable() -> None:
    assert callable(run_full_demo.main)
