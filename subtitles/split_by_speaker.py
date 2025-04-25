import re
from tqdm import tqdm

def split_by_speaker(words, lang_code, max_chars=80, max_duration=4.0, max_repeats=5):
    subs = []
    current = []
    current_speaker = words[0].get('speaker', "")
    current_start = words[0]['start']
    current_end = words[0]['end']
    idx = 1

    for i, word in tqdm(enumerate(words), total=len(words)):
        if not word.get("word"):
            continue

        speaker = word.get("speaker", "")
        word_start = word["start"]
        word_end = word["end"]

        # Check if we should split
        text = _build_subtitle_text(current)
        should_split = (
            speaker != current_speaker or
            len(text) > max_chars or
            (word_end - current_start) > max_duration
        )

        if current and should_split:


            subtitle_text = _build_subtitle_text(current)
            subtitle_text = _clean_repetitions(subtitle_text, max_repeats)
            if subtitle_text:
                current_end = min(current_end, current_start + max_duration)  # Cap to max_duration
                subs.append((idx, current_start, current_end, subtitle_text))
                idx += 1

            current = []
            current_start = word_start
            current_speaker = speaker

        current.append(word)
        current_end = word_end

    # Final subtitle
    if current:
        subtitle_text = " ".join(w["word"] for w in current).strip()
        subtitle_text = _clean_repetitions(subtitle_text, max_repeats)
        if subtitle_text:
            current_end = min(current_end, current_start + max_duration)  # Cap to max_duration
            subs.append((idx, current_start, current_end, subtitle_text))

    return subs

def _is_cjk_char(char):
    """Rudimentary check for CJK characters by Unicode block."""
    return any([
        '\u4e00' <= char <= '\u9fff',  # CJK Unified Ideographs
        '\u3040' <= char <= '\u309f',  # Hiragana
        '\u30a0' <= char <= '\u30ff',  # Katakana
        '\uff00' <= char <= '\uffef',  # Full-width roman + half-width kana
    ])

def _is_mostly_cjk(text, threshold=0.5):
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return cjk_count / max(1, len(text)) > threshold

def _build_subtitle_text(words):
    raw_text = "".join(w["word"] for w in words).strip()
    if _is_mostly_cjk(raw_text):
        return raw_text
    else:
        return " ".join(w["word"] for w in words).strip()



def _clean_repetitions(text, max_repeats=5):
    # Collapse long runs of the same character (like ー or え)
    return re.sub(r'(.)\1{'+str(max_repeats)+r',}', lambda m: m.group(1) * max_repeats + '…', text)
