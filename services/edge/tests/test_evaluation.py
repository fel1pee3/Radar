from radar_edge.evaluation import Interval, Target, match_episodes


def test_evaluation_rejects_duplicate_files_and_calibration_session_leakage():
    import json
    from pathlib import Path

    import pytest
    from pydantic import ValidationError

    from radar_edge.evaluation import Manifest

    example = json.loads(
        (Path(__file__).parents[1] / "evaluation.example.json").read_text(encoding="utf-8")
    )
    original = example["videos"][0]
    example["videos"].append({**original, "videoId": "another-clip"})
    with pytest.raises(ValidationError):
        Manifest.model_validate(example)
    example["videos"][1].update(sha256="1" * 64, role="EVALUATION")
    with pytest.raises(ValidationError):
        Manifest.model_validate(example)
    example["videos"][1]["sessionId"] = "independent-session"
    assert len(Manifest.model_validate(example).videos) == 2


def test_missed_targets_require_complete_annotations():
    target = Target(startMs=0, endMs=4000, kind="PERSON_ON_FLOOR")
    assert match_episodes([], [target], [], 4000)["PERSON_ON_FLOOR"]["missed"] == 1
    assert match_episodes([], [target], [], 4000, False)["PERSON_ON_FLOOR"]["missed"] is None


def test_episode_matching_counts_duplicates_exclusions_and_zero_denominators():
    targets = [
        Target(
            startMs=1000,
            endMs=4000,
            kind="PERSON_ON_FLOOR",
            assistanceNeeded=False,
            confounder="voluntary_floor",
        )
    ]
    events = [{"kind": "PERSON_ON_FLOOR", "sourceOffsetMs": t} for t in [3000, 5000, 7000, 9000]]
    result = match_episodes(events, targets, [Interval(startMs=8000, endMs=10000)], 6000)
    floor = result["PERSON_ON_FLOOR"]
    assert floor["matched"] == 1 and floor["duplicates"] == 1 and floor["unmatchedAlerts"] == 1
    assert floor["inconclusiveAlerts"] == 1 and floor["detectorLatencyMs"] == [2000]
    assert floor["recall"] == 1 and floor["precision"] == 1 / 3
    assert floor["falseAlertsPerHour"] == 600
    assert result["POSSIBLE_FALL"]["recall"] is None
    assert result["POSSIBLE_FALL"]["precision"] is None
    assert match_episodes([], [], [], 0)["PERSON_ON_FLOOR"]["falseAlertsPerHour"] is None


def test_unannotated_video_is_not_reported_as_perfect_negative():
    result = match_episodes(
        [{"kind": "PERSON_ON_FLOOR", "sourceOffsetMs": 3000}], [], [], 10000, False
    )
    assert result["PERSON_ON_FLOOR"]["recall"] is None
    assert result["PERSON_ON_FLOOR"]["precision"] is None
    assert result["PERSON_ON_FLOOR"]["inconclusiveAlerts"] == 1


def test_target_overlapping_exclusion_is_inconclusive_even_outside_hidden_subinterval():
    target = Target(startMs=1000, endMs=5000, kind="PERSON_ON_FLOOR")
    r = match_episodes(
        [{"kind": "PERSON_ON_FLOOR", "sourceOffsetMs": 4000}],
        [target],
        [Interval(startMs=1500, endMs=2000)],
        1000,
    )
    assert r["PERSON_ON_FLOOR"]["targetsExcluded"] == 1
    assert r["PERSON_ON_FLOOR"]["inconclusiveAlerts"] == 1
    assert r["PERSON_ON_FLOOR"]["unmatchedAlerts"] == 0
