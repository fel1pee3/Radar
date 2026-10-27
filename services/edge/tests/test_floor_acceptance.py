"""Primary denominator must include missed/unobservable targets."""

from radar_edge.evaluation import Interval, Target, match_floor_acceptance


def test_exclusion_cannot_remove_missed_target_or_silence_unknown_scene():
    target = Target(startMs=0, endMs=10000, kind="PERSON_ON_FLOOR")
    result = match_floor_acceptance([], [target], [Interval(startMs=0, endMs=10000)], 0, 10000)
    assert result["targets"] == 1 and result["missed"] == 1
    assert result["targetsOverlappingExclusions"] == 1 and not result["approved"]
    negative = match_floor_acceptance([], [], [], 0, 10000)
    assert negative["negativeResult"] == "INCONCLUSIVE" and not negative["approved"]


def test_latency_is_from_annotation_and_late_or_duplicate_fails_acceptance():
    target = Target(startMs=1000, endMs=10000, kind="PERSON_ON_FLOOR")
    events = [
        {"kind": "POSSIBLE_FALL", "sourceOffsetMs": 7000},
        {"kind": "PERSON_ON_FLOOR", "sourceOffsetMs": 8000},
    ]
    result = match_floor_acceptance(events, [target], [], 10000, 10000)
    assert result["latenciesMs"] == [6000] and result["late"] == 1
    assert result["duplicates"] == 1 and not result["approved"]
    assert not result["transitionAccuracyEvaluated"]


def test_annotated_empty_scene_requires_healthy_capture_not_an_invented_pose():
    result = match_floor_acceptance(
        [], [], [], 0, 10000, negative_expected_person=False, capture_eligible_ms=10000
    )
    assert result["negativeResult"] == "PASS" and result["eligibleFraction"] == 0
    result = match_floor_acceptance(
        [], [], [], 0, 10000, negative_expected_person=False, capture_eligible_ms=0
    )
    assert result["negativeResult"] == "INCONCLUSIVE" and not result["approved"]


def test_already_lying_clip_cannot_validate_an_unobserved_fall_transition():
    target = Target(startMs=0, endMs=10000, kind="PERSON_ON_FLOOR", transitionObserved=False)
    result = match_floor_acceptance(
        [{"kind": "POSSIBLE_FALL", "sourceOffsetMs": 2000}], [target], [], 10000, 10000
    )
    assert result["matched"] == 1 and result["unjustifiedTransitionAlerts"] == 1
    assert result["transitionAccuracyEvaluated"] and not result["approved"]


def test_unobserved_source_tail_cannot_inflate_positive_coverage():
    target = Target(startMs=0, endMs=10000, kind="PERSON_ON_FLOOR")
    result = match_floor_acceptance(
        [{"kind": "PERSON_ON_FLOOR", "sourceOffsetMs": 2000}],
        [target],
        [],
        2000,
        2000,
        evaluation_duration_ms=10000,
    )
    assert result["observedMs"] == 2000
    assert result["evaluatedDurationMs"] == 10000
    assert result["eligibleFraction"] == 0.2
    assert not result["approved"]


def test_short_healthy_capture_does_not_certify_full_empty_video():
    result = match_floor_acceptance(
        [],
        [],
        [],
        0,
        2000,
        negative_expected_person=False,
        capture_eligible_ms=2000,
        evaluation_duration_ms=10000,
    )
    assert result["negativeResult"] == "INCONCLUSIVE"
    assert not result["approved"]
