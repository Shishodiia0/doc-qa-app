import numpy as np
import faiss
import hashlib
from typing import List, Tuple, Optional

EMBED_DIM = 256


def _tfidf_embed(texts: List[str]) -> np.ndarray:
    """Lightweight deterministic TF-IDF style embedding — no external models."""
    vocab: dict = {}
    tokenized = []
    for text in texts:
        tokens = text.lower().split()
        tokenized.append(tokens)
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)

    vectors = np.zeros((len(texts), EMBED_DIM), dtype=np.float32)
    for i, tokens in enumerate(tokenized):
        tf: dict = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        for t, count in tf.items():
            # map token to a bucket in EMBED_DIM via hash
            idx = int(hashlib.md5(t.encode()).hexdigest(), 16) % EMBED_DIM
            vectors[i][idx] += count / max(len(tokens), 1)

    # L2 normalise
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return vectors / norms


async def embed_texts(texts: List[str]) -> np.ndarray:
    return _tfidf_embed(texts)


def build_faiss_index(vectors: np.ndarray) -> faiss.IndexFlatL2:
    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(vectors)
    return index


async def search_chunks(
    query: str,
    chunks: List[str],
    index: faiss.IndexFlatL2,
    top_k: int = 5,
) -> List[Tuple[int, str]]:
    q_vec = _tfidf_embed([query])
    distances, indices = index.search(q_vec, min(top_k, len(chunks)))
    results = []
    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            results.append((int(idx), chunks[idx]))
    return results


def find_timestamp_for_answer(answer: str, segments) -> Optional[float]:
    if not segments:
        return None
    answer_lower = answer.lower()
    best_seg = None
    best_score = 0
    for seg in segments:
        text = seg["text"] if isinstance(seg, dict) else seg.text
        words = text.lower().split()
        score = sum(1 for w in words if w in answer_lower)
        if score > best_score:
            best_score = score
            best_seg = seg
    if not best_seg or best_score == 0:
        return None
    return best_seg["start"] if isinstance(best_seg, dict) else best_seg.start
