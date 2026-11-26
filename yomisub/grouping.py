"""Language grouping over exact Unicode surfaces. Time and ownership stay separate."""

from functools import cached_property
from importlib.metadata import version

from .domain import TextSpan
from .ports import Grouping


def whole(segment, diagnostic=None):
    return Grouping(segment.id, (TextSpan(0, len(segment.text)),), (), "segment", diagnostic=diagnostic)


def lexical_join(segment):
    pieces = tuple(p for p in segment.pieces if p.span is not None)
    cursor = 0
    for piece in pieces:
        if piece.span.start != cursor or segment.text[cursor:piece.span.end] != piece.surface:
            return ()
        cursor = piece.span.end
    return pieces if cursor == len(segment.text) else ()


def time_edges(segment, pieces):
    """Candidate adjacency only. Recording bounds and audible support belong to spotting."""
    edges = set()
    for left, right in zip(pieces, pieces[1:]):
        times = (segment.timing.start, left.timing.start, left.timing.end, right.timing.start,
                 right.timing.end, segment.timing.end)
        if all(t is not None for t in times) and times[0] <= times[1] < times[2] <= times[3] < times[4] <= times[5]:
            edges.add(left.span.end)
    return edges


def grammatical_edges(morphs):
    edges = []
    for left, right in zip(morphs, morphs[1:]):
        part = right.part_of_speech()[0]
        if left.surface() in ("。", "！", "？", "!", "?"):
            edges.append(left.end())
        elif part not in {"助詞", "助動詞", "補助記号", "接尾辞"} and (
            left.surface() in {"、", "，", ","} or
            (left.surface() == "は" and right.surface() not in {"ない", "あり", "いけ", "なら"})
        ):
            edges.append(left.end())
    for left, blank, right in zip(morphs, morphs[1:], morphs[2:]):
        if (blank.surface().isspace() and left.part_of_speech()[0] != "接頭辞"
                and right.part_of_speech()[0] not in {"助詞", "助動詞", "接尾辞", "補助記号"}):
            edges.append(blank.begin())
    return tuple(sorted(set(edges)))


class PhraseGrouping:
    @cached_property
    def tokenizer(self):
        from sudachipy import Dictionary

        return Dictionary().tokenizer()

    @cached_property
    def versions(self):
        return version("SudachiPy"), version("SudachiDict-core")

    def group(self, transcript, language):
        if language not in {"ja", "jpn"}:
            return tuple(whole(seg) for seg in transcript.segments)
        return tuple(self.japanese(seg) for seg in transcript.segments)

    def japanese(self, segment):
        from sudachipy import SplitMode

        pieces = lexical_join(segment)
        if not pieces:
            return whole(segment, "Whisper pieces did not reconstruct the segment surface.")
        morphs = list(self.tokenizer.tokenize(segment.text, SplitMode.C))
        spans = tuple(TextSpan(m.begin(), m.end()) for m in morphs)
        if ''.join(m.surface() for m in morphs) != segment.text or any(
            segment.text[s.start:s.end] != m.surface() for s,m in zip(spans,morphs)
        ):
            return whole(segment, "Sudachi surfaces did not reconstruct the segment.")
        joins = tuple(tuple(p.id for p in pieces if p.span.start < s.end and s.start < p.span.end)
                      for s in spans)
        wraps = grammatical_edges(morphs)
        timed = time_edges(segment,pieces)
        return Grouping(segment.id,spans,tuple(w for w in wraps if w in timed),"sudachi",
                        wraps,joins,*self.versions,"C")
