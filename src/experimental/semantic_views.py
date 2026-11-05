"""Semantic search boundaries, never replacement citable evidence."""
from src.semantic_chunking_adapter import chunk_passages
from .search_chunks import make_search_views, record_hash


def make_semantic_views(parents, encoder):
    """Map bounded semantic views back to exact original-parent coordinates.

    Structured table rows and figures bypass semantic splitting. Their bounded
    token views still resolve to the complete original evidence record.
    """
    views = []
    for parent in parents:
        atomic = parent.get('representation') == 'linearized_table' or parent.get('table_id') or parent['source'] == 'tex_figure'
        children = [parent] if atomic else chunk_passages([parent], encoder)
        for child in children:
            offset = 0 if child is parent else child['parent_text_start']
            for view in make_search_views([child], encoder.tokenizer):
                view.update(parent_chunk_id=parent['chunk_id'],
                            view_id=f"{parent['chunk_id']}__semantic224_{len(views):06d}",
                            char_start=offset + view['char_start'],
                            char_end=offset + view['char_end'],
                            parent_record_sha256=record_hash(parent))
                views.append(view)
    return views
