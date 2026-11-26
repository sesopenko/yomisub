"""Preserve shared diarization boundaries when writing onset-plus-duration RTTM."""

from decimal import Decimal


def rttm(annotation):
    rows = []
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        start = Decimal(str(turn.start))
        duration = Decimal(str(turn.end)) - start
        rows.append(f"SPEAKER {annotation.uri} 1 {start:f} {duration:f} <NA> <NA> {speaker} <NA> <NA>")
    return "\n".join(rows)
