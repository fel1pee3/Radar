"""Observed body support in a calibrated 2D image. Never physical contact/height.

V4 is opt-in. No enlargement of polygons, box intersection or synthetic joints.
Limits are fixed before the full comparison: >=6 essential points, >=3 torso,
one complete anatomical side; floor support distributed over >=3 real points,
including a torso point, spanning >=25% of the observed body diagonal.
"""

import math
from dataclasses import replace

from radar_edge.features import inside_polygon
from radar_edge.observations import point_usable

TORSO = {11, 12, 23, 24}
SIDES = ({11, 23, 25, 27}, {12, 24, 26, 28})


def observed_geometry(valid, width, height):
    shoulders = [valid[i] for i in (11, 12) if i in valid]
    hips = [valid[i] for i in (23, 24) if i in valid]
    if not shoulders or not hips:
        return None
    sx = sum(p.x for p in shoulders) / len(shoulders)
    sy = sum(p.y for p in shoulders) / len(shoulders)
    hx = sum(p.x for p in hips) / len(hips)
    hy = sum(p.y for p in hips) / len(hips)
    dx, dy = (hx - sx) * width, (hy - sy) * height
    xs, ys = [p.x * width for p in valid.values()], [p.y * height for p in valid.values()]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if min(w, h, math.hypot(dx, dy)) <= 1e-6:
        return None
    return dict(
        hipX=hx,
        hipY=hy,
        shoulderX=sx,
        shoulderY=sy,
        torsoAngleDeg=math.degrees(math.atan2(abs(dx), abs(dy))),
        bboxAspectRatio=h / w,
        bodyScale=math.hypot(w, h) / height,
    )


def apply_body_context(classifier, observation, classified, valid, *, geometry_fallback=True):
    """Keep class scores separate from deterministic geometry and context decisions."""
    o, f = observation, classified
    geometry = observed_geometry(valid, o.width, o.height)
    sufficient = (
        len(valid) >= 6
        and {23, 24} <= valid.keys()
        and len(TORSO & valid.keys()) >= 3
        and any(side <= valid.keys() for side in SIDES)
        and geometry is not None
    )
    points = {
        p.index: p
        for p in o.poses[0].landmarks
        if 11 <= p.index <= 28
        and point_usable(p, classifier.artifact.qualityThreshold, o.poses[0].qualitySource)
        and 0 <= p.x <= 1
        and 0 <= p.y <= 1
    }
    floor_points = {
        i for i, p in points.items() if inside_polygon(p.x, p.y, classifier.calibration_floor)
    }
    exclusions = [
        *classifier.settings.excludedRegions,
        *(r.polygon for r in classifier.settings.supportRegions),
    ]
    # A torso inside a configured support prevents floor confirmation even if feet
    # or hands reach the floor. A single hand overlapping furniture does not prove support.
    excluded = any(
        inside_polygon(points[i].x, points[i].y, poly)
        for i in TORSO & points.keys()
        for poly in exclusions
    )
    spread = max(
        (
            math.hypot(
                (points[a].x - points[b].x) * o.width, (points[a].y - points[b].y) * o.height
            )
            for a in floor_points
            for b in floor_points
        ),
        default=0,
    )
    distributed = bool(
        geometry
        and len(floor_points) >= 3
        and TORSO & floor_points
        and spread >= 0.25 * geometry["bodyScale"] * o.height
    )
    # Hip projection remains reported honestly even when support comes from other joints.
    hip_floor = (
        inside_polygon(f.hipX, f.hipY, classifier.calibration_floor)
        if f.hipX is not None and f.hipY is not None
        else None
    )
    # A complete observed arm can lie on the calibrated image floor even when
    # all torso projections sit above its boundary. This is an opt-in alternative
    # 2D grounding cue, not a margin, virtual landmark or physical-contact claim.
    # Full torso/knees and the existing body sufficiency guard remain mandatory.
    arm_grounded = False
    if (
        classifier.settings.floorContextStrategy == "ARTICULATED_ARM_V1"
        and sufficient
        and geometry is not None
        and TORSO | {25, 26} <= valid.keys()
    ):
        diagonal = geometry["bodyScale"] * o.height
        for shoulder, elbow, wrist in ((11, 13, 15), (12, 14, 16)):
            if {shoulder, elbow, wrist} <= points.keys() and {elbow, wrist} <= floor_points:
                forearm = math.hypot(
                    (points[elbow].x - points[wrist].x) * o.width,
                    (points[elbow].y - points[wrist].y) * o.height,
                )
                if forearm >= 0.1 * diagonal:
                    arm_grounded = True
    compatible = sufficient and not excluded and (hip_floor is True or distributed or arm_grounded)
    support_mechanism = (
        "EXCLUDED"
        if excluded
        else "HIP_PROJECTION"
        if compatible and hip_floor is True
        else "DISTRIBUTED_POINTS"
        if compatible and distributed
        else "OBSERVED_ARM_CHAIN_2D"
        if compatible and arm_grounded
        else "UNKNOWN"
    )
    posture, origin = f.posture, f.postureEvidenceOrigin
    # Independent geometric branch for supine torso with both knees above pelvis:
    # relevant to exercises with flexed/raised legs. Does not change learned scores.
    # Conservative full torso and knees, same 60 degree baseline horizontal threshold.
    raised_knees = bool(
        sufficient
        and geometry
        and TORSO | {25, 26} <= valid.keys()
        and geometry["torsoAngleDeg"] >= 60
        and all(valid[i].y <= geometry["hipY"] - 0.1 * geometry["bodyScale"] for i in (25, 26))
    )
    if geometry_fallback and compatible and raised_knees and posture in {"UNKNOWN", "SEATED"}:
        posture, origin = "LYING", "OBSERVED_RECLINED_TORSO_RAISED_KNEES_V4"
    observed_upright = (
        geometry["shoulderY"] < geometry["hipY"] and geometry["torsoAngleDeg"] <= 55.0
        if geometry is not None and TORSO <= valid.keys()
        else None
    )
    # Separate uncertainty about a subtype from a strongly supported class group.
    # This is NOT a normal-activity claim: exact scores and subtype uncertainty
    # remain visible, and a missing body or meaningful lying score stays UNKNOWN.
    subtype_uncertain = False
    class_scores = f.postureClassScores
    if (
        classifier.settings.postureAmbiguityStrategy == "NON_FLOOR_GROUP_V1"
        and posture == "UNKNOWN"
        and sufficient
        and observed_upright is True
        and len(class_scores) == 4
        and sum(class_scores[:3]) >= 0.95
        and class_scores[3] <= 0.05
    ):
        posture, origin = "OTHER_POSTURE", "RTMO_NON_FLOOR_GROUP_V1"
        subtype_uncertain = True
    reasons = []
    if posture == "UNKNOWN":
        reasons.append("POSTURE_UNCERTAIN")
    if posture == "LYING":
        if not sufficient:
            reasons.append("FLOOR_BODY_EVIDENCE_INCOMPLETE")
        if excluded:
            reasons.append("CONTEXT_EXCLUDED_REGION")
        elif not compatible:
            reasons.append("FLOOR_CONTEXT_UNKNOWN")
    # Observed image orientation is separate from posture classification.
    # It does not relabel posture; unresolved UNKNOWN remains ineligible.
    # Four current usable torso joints are required;
    # missing joints never acquire a temporal orientation value.
    return replace(
        f,
        **(geometry or {}),
        posture=posture,
        postureEvidenceOrigin=origin,
        eligible=not reasons,
        candidate=posture == "LYING" and not reasons,
        reasons=tuple(reasons),
        hipInFloorZone=hip_floor,
        regionState="EXCLUDED" if excluded else "BODY_SUPPORTED_2D" if compatible else "UNKNOWN",
        bodyEvidenceSufficient=sufficient,
        floorContextCompatible=bool(compatible),
        contextEvidenceIndices=tuple(sorted(floor_points)),
        contextSupportMechanism=support_mechanism,
        observedUprightTorso=observed_upright,
        postureSubtypeUncertain=subtype_uncertain,
    )
