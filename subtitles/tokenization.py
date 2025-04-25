from sudachipy import dictionary, tokenizer
# pip install sudachipy sudachidict-core

_tokenizer_obj = None

def _get_sudachi_tokenizer():
    global _tokenizer_obj
    if _tokenizer_obj is None:
        _tokenizer_obj = dictionary.Dictionary().create()
    return _tokenizer_obj

def group_japanese_words(aligned_chars):
    full_text = ''.join(c["word"] for c in aligned_chars)
    starts = [c["start"] for c in aligned_chars]
    ends = [c["end"] for c in aligned_chars]

    tokenizer_obj = _get_sudachi_tokenizer()
    mode = tokenizer.Tokenizer.SplitMode.C  # Best for "subtitle-style" segmentation

    new_words = []
    pos = 0

    for token in tokenizer_obj.tokenize(full_text, mode):
        surface = token.surface()
        length = len(surface)

        chars = aligned_chars[pos:pos + length]
        if not chars:
            pos += length
            continue

        new_words.append({
            "word": surface,
            "start": chars[0]["start"],
            "end": chars[-1]["end"],
            "speaker": chars[0].get("speaker", "")
        })

        pos += length

    return new_words
