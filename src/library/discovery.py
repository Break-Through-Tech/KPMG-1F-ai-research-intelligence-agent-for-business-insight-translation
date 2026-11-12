"""Topic-balanced arXiv discovery with resumable, recorded pagination."""
from src.arxiv_collection import parse_feed

from .arxiv_client import API

DATE_FILTER = 'submittedDate:[202401010000 TO 202612312359]'  # recent papers usually have arXiv HTML
TOPICS = {
    'llm': ('Large language models', '(cat:cs.CL OR cat:cs.LG) AND abs:"large language model"'),
    'rag': ('Retrieval-augmented generation', 'abs:"retrieval-augmented generation" OR abs:"retrieval augmented generation"'),
    'agents': ('AI agents', '(cat:cs.AI OR cat:cs.CL OR cat:cs.MA) AND (abs:"LLM agents" OR abs:"language agents" OR abs:"agentic")'),
    'healthcare': ('Healthcare AI', '(abs:clinical OR abs:medical OR abs:healthcare) AND (abs:"language model" OR abs:LLM)'),
    'finance': ('Finance AI', '(abs:financial OR abs:finance OR abs:banking) AND (abs:"language model" OR abs:LLM)'),
    'security': ('AI security', 'cat:cs.CR AND (abs:"language model" OR abs:LLM OR abs:jailbreak)'),
    'governance': ('AI governance', 'abs:"AI governance" OR abs:"AI regulation" OR abs:"AI policy" OR abs:"responsible AI" OR abs:"AI accountability"'),
}
RELEVANT_PREFIXES = ('cs.', 'stat.ML', 'q-fin.', 'eess.', 'econ.', 'q-bio.')


def topic_query(topic):
    return f'({TOPICS[topic][1]}) AND {DATE_FILTER}'


def relevant(record):
    return any(c.strip().startswith(RELEVANT_PREFIXES) for c in record['categories'].split(','))


def discover(store, client, *, per_topic=200, page_size=100, topics=None, log=print):
    """Fetch up to per_topic candidates per topic. Fetched pages are skipped on resume."""
    summary = {}
    for topic in (topics or TOPICS):
        query = topic_query(topic)
        counts = {'new': 0, 'seen': 0, 'newer_version': 0, 'irrelevant': 0}
        for start in range(0, per_topic, page_size):
            if store.page_done(topic, start):
                continue
            status, body = client.get(API, params={'search_query': query, 'start': start,
                                                   'max_results': page_size, 'sortBy': 'relevance'})
            if status != 200:
                raise RuntimeError(f'arXiv search returned HTTP {status} for {topic} page {start}.')
            records, total = parse_feed(body)
            for rank, record in enumerate(records, start=start):
                if not relevant(record):
                    counts['irrelevant'] += 1
                    continue
                counts[store.upsert_candidate(record, topic, rank)] += 1
            store.record_page(topic, start, query, len(records), total)
            store.event('discovery_page', None, f'{topic} start={start} results={len(records)} total={total}')
            store.commit()
            log(f'discovery {topic} start={start}: {len(records)} records (total {total})')
            if len(records) < page_size or start + page_size >= total:
                break
        summary[topic] = counts
    return summary
