"""Problem 3 (bm25), v1 — Ning's design.

Inverted index: term -> list of (doc_id, times the term occurs in the doc, doc length),
plus two corpus-wide numbers, N and avgdl. Built in one pass over the docs.
Search reads only the query terms' lists, scores, then sorts.
"""
from __future__ import annotations

import math
from collections import Counter

from cs329z_hw1.tokenizer import tokenize

K1, B = 1.5, 0.75


class BM25Index:
    def __init__(self, docs: list[str]) -> None:
        self.postings: dict[str, list[tuple[int, int, int]]] = {}
        total_len = 0
        for doc_id, text in enumerate(docs):
            tokens = tokenize(text)
            length = len(tokens)
            total_len += length
            for term, times in Counter(tokens).items():
                self.postings.setdefault(term, []).append((doc_id, times, length))
        self.N = len(docs)
        self.avgdl = total_len / self.N if self.N else 0.0

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        scores: dict[int, float] = {}
        for term in set(tokenize(query)):
            plist = self.postings.get(term)
            if not plist:
                continue
            n_t = len(plist)
            idf = math.log((self.N - n_t + 0.5) / (n_t + 0.5) + 1)
            for doc_id, times, length in plist:
                norm = K1 * (1 - B + B * length / self.avgdl) if self.avgdl else K1
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * times * (K1 + 1) / (times + norm)
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [(int(d), float(s)) for d, s in ranked[:k]]
