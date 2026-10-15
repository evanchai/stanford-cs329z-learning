"""Estimate the autograded score (out of 88) from a local pytest run.

    uv run python score.py            # deterministic tests only (free, exact)
    uv run python score.py --live     # also live tests (calls the model)

Follows the handout's Section 7 table: each problem's deterministic and live
points are scaled by the fraction of those tests that pass. Two limits:
sim_eval is approximated as all-or-nothing on its live test (the real rule is
16+/20 conversations, minus 1 point per conversation below 16), and staff grade
live tests on held-out data with the course models, so a live score here is an
estimate, more so when CS329Z_BACKEND is not openrouter.
"""
import subprocess, sys, tempfile, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

POINTS = {  # problem: (deterministic, live)
    "priority": (1, 2), "daily_digest": (1, 3), "bm25": (8, 0), "email_qa": (2, 6),
    "tool_registry": (3, 0), "tool_protocol": (2, 2), "agent_loop": (8, 0), "cardinal": (2, 0),
    "search_docs": (2, 3), "terminal": (2, 4), "compaction": (5, 3), "memory": (3, 5),
    "interactive": (7, 0), "guardrails": (2, 2), "sim_eval": (0, 10),
}


def run(marker: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        xml = Path(d) / "r.xml"
        subprocess.run([sys.executable, "-m", "pytest", "-m", marker, "-q", "-p", "no:cacheprovider",
                        f"--junitxml={xml}"], check=False)
        res = defaultdict(lambda: [0, 0])  # problem -> [passed, total]
        for tc in ET.parse(xml).getroot().iter("testcase"):
            prob = tc.get("classname", "").split(".")[-1].removeprefix("test_")
            if prob not in POINTS:
                continue
            bad = any(c.tag in ("failure", "error") for c in tc)
            skipped = any(c.tag == "skipped" for c in tc)
            if skipped:
                continue
            res[prob][1] += 1
            res[prob][0] += 0 if bad else 1
        return res


def main() -> None:
    live = "--live" in sys.argv
    det = run("not live")
    lv = run("live") if live else {}
    total = 0.0
    print(f"\n{'problem':<15}{'det':>12}{'live':>12}{'points':>10}")
    for p, (dp, lp) in POINTS.items():
        dpass, dtot = det.get(p, (0, 0))
        s = dp * (dpass / dtot if dtot else 0)
        lcol = "-"
        if lp:
            if live:
                lpass, ltot = lv.get(p, (0, 0))
                s += lp * (lpass / ltot if ltot else 0)
                lcol = f"{lpass}/{ltot}"
            else:
                lcol = "not run"
        total += s
        print(f"{p:<15}{f'{dpass}/{dtot}':>12}{lcol:>12}{s:>7.1f}/{dp + lp}")
    print(f"{'autograded':<39}{total:>7.1f}/88")
    if not live:
        print("Live points (40) not included; run with --live.")


if __name__ == "__main__":
    main()
