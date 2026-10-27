from radar_edge.stream_acceptance import assess_stream_timing


def records(timestamp, ready_age=100, eligible=True):
    return [
        {
            "recordType": "DECISION",
            "timestampMs": timestamp,
            "quality": {"eligible": eligible, "reasons": []},
            "timing": {"frameAgeAtAnalysisStartMs": 0, "capturedFrameAgeAtDecisionMs": ready_age},
            "emission": None,
        },
        {
            "recordType": "PROCESSING_PROFILE",
            "timestampMs": timestamp,
            "monotonicStartNs": 10**12 + timestamp * 10**6,
        },
    ]


def test_eof_stall_is_not_hidden_by_small_media_gaps():
    result = assess_stream_timing(records(0) + records(200) + records(400, 725381), 10400, 10**12)
    assert not result["timingGate"]
    assert result["staleDecisions"] == 1
    assert result["unobservedTailMs"] == 10000
    assert result["timelyEligibleMediaMs"] == 200
    assert result["maxDecisionHostGapMs"] > 725000


def test_monotonic_origin_units_and_utc_clock_changes():
    trace = records(0) + records(200)
    trace[0]["recordedAt"] = "2030-01-01T00:00:00Z"
    result = assess_stream_timing(trace, 400, 10**12)
    assert result["timingGate"]
    assert result["maxDecisionHostGapMs"] == 200
    assert result["lastDecisionFromOriginMs"] == 300


def test_missing_or_nonfinite_timing_is_unverifiable():
    trace = records(0)
    trace[0]["timing"]["capturedFrameAgeAtDecisionMs"] = float("nan")
    assert not assess_stream_timing(trace, 200, 10**12)["timingGate"]
    assert not assess_stream_timing([], 200, 10**12)["timingGate"]


def test_current_age_does_not_bridge_a_wall_interruption():
    trace = records(0) + records(200)
    trace[3]["monotonicStartNs"] += 700 * 10**6
    result = assess_stream_timing(trace, 400, 10**12)
    assert result["timelyEligibleMediaMs"] == 0
    assert result["decisionHostGapsAbove500"] == 1


def test_paired_finish_clock_avoids_start_preparation_error():
    trace = records(0) + records(200)
    for row in trace:
        if row["recordType"] == "PROCESSING_PROFILE":
            row["monotonicFinishedNs"] = row["monotonicStartNs"] + 100 * 10**6
            row["frameAgeAfterPreviewMs"] = 100
            row["monotonicStartNs"] -= 30 * 10**6
    result = assess_stream_timing(trace, 400, 10**12)
    assert result["lastDecisionFromOriginMs"] == 300
    assert result["decisionCoverage"] == 0.5


def test_scheduled_start_age_can_be_negative_but_finish_clock_is_reconstructable():
    trace = records(0) + records(200)
    trace[0]["timing"]["frameAgeAtAnalysisStartMs"] = -3
    trace[1]["monotonicFinishedNs"] = 10**12 + 100 * 10**6
    trace[1]["frameAgeAfterPreviewMs"] = 100
    result = assess_stream_timing(trace, 400, 10**12)
    assert result["timingGate"]
    assert result["negativeStartAgesRecorded"] == 1
    assert result["missingTimingDecisions"] == 0
