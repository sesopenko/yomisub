"""Offline comparison of displayed subtitles with independent recording-local references."""

import argparse
from dataclasses import dataclass
from datetime import timedelta
from functools import cache
import json
from itertools import permutations
from pathlib import Path
import re
from statistics import median
import unicodedata

import srt


@dataclass(frozen=True)
class Display:
    start: int
    end: int
    text: str
    owner: str | None = None


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold()
                   if not c.isspace() and not unicodedata.category(c).startswith('P'))


def displays_from_srt(path):
    def milliseconds(delta):
        return delta // timedelta(milliseconds=1)

    return [Display(milliseconds(cue.start), milliseconds(cue.end), line)
            for cue in srt.parse(path.read_text(encoding='utf-8-sig'))
            for line in cue.content.splitlines() if line.strip()]


def text_runs(displays):
    """Carry an unchanged line across touching states even when a second line enters."""
    runs = []
    last = {}
    for line in sorted(displays, key=lambda d: d.start):
        key = (line.owner, line.text)
        index = last.get(key)
        if index is not None and runs[index].end == line.start:
            runs[index] = Display(runs[index].start, line.end, line.text, line.owner)
        else:
            last[key] = len(runs)
            runs.append(line)
    return runs


def candidates(runs, forms, window):
    # Build each possible continuous reading. A partial surface may span touching
    # states of the same owner. Two simultaneous lines cannot be concatenated.
    def extend(index, prefix, path):
        run = runs[index]
        text = prefix + normalized(run.text)
        for form in forms:
            for match in re.finditer(re.escape(form), text):
                if match.start() < len(normalized(runs[path[0]].text)) and match.end() > len(prefix):
                    yield (runs[path[0]].start, run.end, path, match.start(), match.end(), run.owner)
        if len(text) >= len(normalized(runs[path[0]].text)) + max(map(len, forms)) - 1:
            return
        for j in range(index + 1, len(runs)):
            after = runs[j]
            if after.start > run.end:
                break
            if after.start == run.end and after.owner == run.owner and after.start < window[1]:
                yield from extend(j, text, (*path, j))

    for i, run in enumerate(runs):
        if run.end > window[0] and run.start < window[1] and normalized(run.text):
            yield from extend(i, '', (i,))


def score_phrases(references, displays, *, owner_map=None):
    """Reference order is the expected order within each exchange and speaker."""
    runs = text_runs(displays)
    occupied = set()
    cursor = {}
    results = {}
    for ref in references:
        exchange = (tuple(ref['window_ms']), ref.get('owner'))
        match = None
        forms = tuple(filter(None, map(normalized, ref['forms'])))
        for start, end, path, left, right, owner in sorted(candidates(runs, forms, exchange[0])):
            if (start, left) < cursor.get(exchange, (-1, -1)):
                continue
            chars = [(i, n) for i in path for n in range(len(normalized(runs[i].text)))]
            used = set(chars[left:right])
            if used.isdisjoint(occupied):
                occupied.update(used)
                cursor[exchange] = (start, left)
                match = Display(start, end, '', owner)
                break
        result = {'recovered': match is not None}
        if match:
            result['display_ms'] = [match.start, match.end]
            if match.owner is not None:
                result['display_owner'] = match.owner
            edges = ref.get('speech_edges_ms')
            if edges:
                result['error_ms'] = [match.start - edges[0], match.end - edges[1]]
            if owner_map is None or ref.get('owner') is None:
                result['ownership'] = 'unavailable'
            elif match.owner is None:
                result['ownership'] = 'unresolved'
            else:
                result['ownership'] = ('correct' if owner_map.get(match.owner) == ref['owner']
                                       else 'wrong')
        results[ref['id']] = result
    return results


def map_owners(assignments):
    """Fit one injective correspondence to matched, independently owned phrases."""
    pairs = sorted((actual, expected) for actual, expected in assignments if actual and expected)
    actual_ids = sorted({a for a, _ in pairs})
    expected_ids = sorted({b for _, b in pairs})
    # Only represented IDs need evaluation. Leave extra labels unmatched.
    if len(actual_ids) <= len(expected_ids):
        mappings = (dict(zip(actual_ids, order)) for order in permutations(expected_ids, len(actual_ids)))
    else:
        mappings = (dict(zip(order, expected_ids)) for order in permutations(actual_ids, len(expected_ids)))
    return max(mappings, key=lambda mapping: sum(mapping.get(a) == b for a, b in pairs))


def interval_result(interval, displays, abstentions=()):
    a, b = interval
    visible = [line for line in displays if line.start < b and a < line.end
               and line.text.strip() not in {'[音楽]', '[拍手]', '♪'}]
    if visible:
        return 'displayed'
    if any(x < b and a < y for x, y in abstentions):
        return 'abstained'
    return 'empty'


def overlap_events(expected, observed, tolerance=500):
    """Pair intersecting events with both edges within tolerance, preserving time order."""
    expected = sorted(map(tuple, expected))
    observed = sorted(map(tuple, observed))

    @cache
    def best(i, j):
        if i == len(expected) or j == len(observed):
            return ()
        a, b = expected[i]
        c, d = observed[j]
        choices = [best(i + 1, j), best(i, j + 1)]
        if max(a, c) < min(b, d) and max(abs(a - c), abs(b - d)) <= tolerance:
            choices.append(((i, j),) + best(i + 1, j + 1))
        return min(choices, key=lambda pairs: (
            -len(pairs),
            sum(abs(expected[x][k] - observed[y][k]) for x, y in pairs for k in (0, 1)),
            pairs,
        ))

    pairs = best(0, 0)
    return {'hits': len(pairs), 'misses': len(expected) - len(pairs),
            'false_positives': len(observed) - len(pairs),
            'edge_errors_ms': [[observed[j][k] - expected[i][k] for k in (0, 1)]
                               for i, j in pairs]}


def paired(legacy, rebuilt):
    required = [k for k, v in legacy.items() if v['recovered']]
    lost = [k for k in required if not rebuilt.get(k, {}).get('recovered')]
    timed = [k for k in required if 'error_ms' in legacy[k]]

    def medians(results):
        if not timed or any('error_ms' not in results.get(k, {}) for k in timed):
            return None
        return [median(abs(results[k]['error_ms'][i]) for k in timed) for i in (0, 1)]

    before, after = medians(legacy), medians(rebuilt)
    improved = bool(before and after and before != after and all(a <= b for a, b in zip(after, before)))
    return {'required_ids': required, 'lost_ids': lost, 'timed_ids': timed,
            'legacy_median_abs_ms': before, 'rebuilt_median_abs_ms': after,
            'coverage_pass': not lost, 'timing_pass': improved}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('srt_directory', type=Path)
    args = parser.parse_args()
    cases = json.loads(Path(__file__).with_name('references.json').read_text())['cases']
    results = {}
    for name, case in cases.items():
        lines = displays_from_srt(args.srt_directory / (name + '.ja.srt'))
        results[name] = score_phrases(case['phrases'], lines)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
