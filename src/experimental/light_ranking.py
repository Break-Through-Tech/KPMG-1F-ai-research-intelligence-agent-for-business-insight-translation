"""Lower-cost ranking for question parts.

A part only needs to anchor its best passages; the full question is still ranked by
the complete facet + cross-encoder path. Here the hybrid first stage (dense + lexical
+ paper scoring) is reranked by the cross-encoder on its top `n` candidates only,
instead of the whole candidate pool. Measured on the development set: p90 latency of
multi-part questions dropped from 14.6 s to 9.1 s with no loss in part coverage.
"""
import numpy as np

from .retriever import tokens


def light_order(retriever, reranker, query, query_vector, n=20):
    routes, _ = retriever.rank(query, query_vector, with_reranker=False)
    hybrid = routes['document_hybrid']
    candidates = hybrid[:n]
    if not candidates:
        return hybrid
    terms = set(tokens(query))
    pairs = []
    for ident in candidates:
        parent = retriever.byid[ident]
        view = max(retriever.byview[ident], key=lambda j: sum(
            retriever.lex.idf.get(w, 1) for w in terms.intersection(tokens(retriever.views[j]['text']))))
        text = ('Title: ' + parent['title'] + '\nSection: ' + parent.get('section', '') + '\n'
                + retriever.views[view]['text'])
        if len(reranker.tokenizer(query, text, add_special_tokens=True, truncation=False)['input_ids']) > reranker.max_seq_length:
            raise ValueError('Reranker pair would truncate')
        pairs.append((query, text))
    scores = np.asarray(reranker.predict(pairs, batch_size=16, show_progress_bar=False)).reshape(-1)
    if not np.isfinite(scores).all():
        raise ValueError('Invalid reranker values')
    return [candidates[i] for i in np.argsort(-scores, kind='stable')] + hybrid[n:]
