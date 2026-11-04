"""Export compact audit-friendly results; full texts/vectors remain local."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

from experiments.semantic_calibration.run import norm, summarize


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--corpus',type=Path,required=True)
    ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    corpus=json.loads(args.corpus.read_text())
    protocol=json.loads((args.results/'protocol.json').read_text())
    if hashlib.sha256(args.corpus.read_bytes()).hexdigest()!=protocol['corpus_sha256']:
        raise ValueError('Corpus hash mismatch')
    reports=[json.loads(p.read_text()) for p in sorted(args.results.glob('*/*/report.json'))]
    if len(reports)!=9:
        raise ValueError(f'Expected nine completed model/source runs, found {len(reports)}')
    qs=json.loads((args.results/'questions.json').read_text())
    common_available={q['id'] for q in qs if all(
        all(any(norm(a) in norm(b['text']) for b in corpus['blocks'] if b['source']==s and b['paper']==q['paper']) for a in q['anchors'])
        for s in ('pdf','html','tex'))}
    n_tune=sum(q['split']=='tuning' for q in qs)
    n_validation=sum(q['split']=='validation' for q in qs)
    compact=[]
    lines=['# Matched-source semantic calibration results','',
           '**Development diagnostic, not generated-answer accuracy or a blind test.**', '',
           f"{len(protocol['common_papers'])} versioned papers; {len(qs)} questions ({n_tune} tuning / {n_validation} validation). All 9 model/source runs completed.",
           '11 policies × 4 retrieval conditions × 3 models × 3 formats = 396 ablation cells.', '',
           f'{len(common_available)}/{len(qs)} questions have designated anchors available in every source format.', '',
           '## Tuning-selected semantic policy vs controls (validation only)', '',
           'All methods below have a 1600-token cap. Baseline and token-only use the SAME neighbor setting as the selected policy; neither is tuned.', '',
           '| Model | Source | Selected semantic policy / context | Baseline | Token-only | Selected | Paired wins/losses vs baseline | Mean tokens baseline → selected |',
           '| --- | --- | --- | ---: | ---: | ---: | --- | --- |']
    for report in reports:
        selected=report['selected'];variants=report['variants']
        label,mode=selected['policy'],selected['mode']
        base=[r for r in variants['baseline']['queries'][mode] if r['split']=='validation']
        chosen=[r for r in variants[label]['queries'][mode] if r['split']=='validation']
        token=[r for r in variants['token_only240_overlap32']['queries'][mode] if r['split']=='validation']
        wins=[c['id'] for b,c in zip(base,chosen) if c['complete'] and not b['complete']]
        losses=[c['id'] for b,c in zip(base,chosen) if b['complete'] and not c['complete']]
        bs,cs,ts=map(summarize,(base,chosen,token))
        model=report['model'].split('/')[-1]
        lines.append(f"| {model} | {report['source']} | {label} / {mode} | {bs['complete']}/{len(base)} | {ts['complete']}/{len(base)} | {cs['complete']}/{len(base)} | {len(wins)} / {len(losses)} | {bs['mean_tokens']} → {cs['mean_tokens']} |")
        clean={k:v for k,v in report.items() if k!='variants'}
        clean.update(wins=wins,losses=losses,variants={})
        for name,arm in variants.items():
            small={k:v for k,v in arm.items() if k!='queries'}
            small['outcome_columns']=['question_id','anchor_found_bits','source_available','context_tokens']
            small['outcomes']={m:[[r['id'], ''.join('1' if f else '0' for f in r['found']),r['source_available'],r['tokens']] for r in rows] for m,rows in arm['queries'].items()}
            small['all_formats_available']={m:{split:summarize([r for r in rows if r['id'] in common_available and r['split']==split])
                                                for split in ('tuning','validation')} for m,rows in arm['queries'].items()}
            clean['variants'][name]=small
        compact.append(clean)
    lines+=['', '## Same questions available in every format (validation)', '',
            '| Model | Source | Available validation questions | Baseline | Selected semantic |',
            '| --- | --- | ---: | ---: | ---: |']
    for report in reports:
        selected=report['selected']; mode=selected['mode']; label=selected['policy']
        base=[r for r in report['variants']['baseline']['queries'][mode] if r['split']=='validation' and r['id'] in common_available]
        chosen=[r for r in report['variants'][label]['queries'][mode] if r['split']=='validation' and r['id'] in common_available]
        lines.append(f"| {report['model'].split('/')[-1]} | {report['source']} | {len(base)} | {sum(r['complete'] for r in base)} | {sum(r['complete'] for r in chosen)} |")
    lines+=['', '## Budget and expansion controls (validation, original semantic policy)', '',
            '| Model / source | Original top5 | Original 1600 tokens | Original 1600 + neighbors | Baseline 1600 | Baseline 1600 + neighbors |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
    for report in reports:
        original=report['variants']['original']['summaries']; baseline=report['variants']['baseline']['summaries']
        values=[original[m]['validation']['complete'] for m in ('top5','tokens1600','tokens1600_neighbors')]
        values += [baseline[m]['validation']['complete'] for m in ('tokens1600','tokens1600_neighbors')]
        lines.append(f"| {report['model'].split('/')[-1]} / {report['source']} | "+' | '.join(str(v)+'/'+str(n_validation) for v in values)+' |')
    lines+=['', '## Extraction coverage (matched papers, both question splits)', '',
            '| Source | Available anchors / questions | Missing question IDs |','| --- | --- | --- |']
    for source in ('pdf','html','tex'):
        rows=next(r for r in reports if r['source']==source)['variants']['baseline']['queries']['tokens1600']
        missing=[r['id'] for r in rows if not r['source_available']]
        lines.append(f"| {source} | {len(rows)-len(missing)}/{len(rows)} | {', '.join(missing) or 'none'} |")
    lines+=['','## Full ablations (validation)', '',
            'All variants disclosed; only the tuning-selected row above is a selection-validation result. Do not pick the best validation row after viewing this table.','',
            '| Model / source | Policy | Chunks | Mean chars | Over encoder limit | Top5 | 800 tokens | 1600 tokens | 1600 + neighbors |',
            '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for report in reports:
        for name,arm in report['variants'].items():
            values=[arm['summaries'][m]['validation']['complete'] for m in ('top5','tokens800','tokens1600','tokens1600_neighbors')]
            lines.append(f"| {report['model'].split('/')[-1]} / {report['source']} | {name} | {arm['chunks']} | {arm['mean_chars']} | {arm['over_model_limit']} | "+' | '.join(str(v)+'/'+str(n_validation) for v in values)+' |')
    lines+=['','## Limitations','',
            '- Single development corpus; only nine validation papers, with correlated questions. No statistical superiority claim.',
            '- Exact normalized span containment is a retrieval proxy; no generated-answer/human relevance scoring. See ../QUALITATIVE.md for two scored gains where baseline already supports the answer.',
            '- HTML omits display equations/table bodies; cached TeX is raw parsed source with historical parser provenance, not rendered prose.',
            '- Source-absent spans stay in overall denominators. Paired cross-format available-only results are in compact-results.json.',
            '- Over-limit atomic sentences/math are retained; encoder truncation is counted. Context windows are never truncated.',
            '- Shared cached embeddings/MPS timings are not production latency measurements. Defaults and persistent index are unchanged.',
            '', 'See protocol.json, compact-results.json, questions.json and source-receipts.json for reproducibility metadata. Full source blocks, contexts and vectors remain in the local artifact directory.']
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    (args.output/'compact-results.json').write_text(json.dumps(compact,indent=2))
    (args.output/'protocol.json').write_text(json.dumps(protocol,indent=2))
    (args.output/'questions.json').write_text(json.dumps(qs,indent=2,ensure_ascii=False))
    (args.output/'source-receipts.json').write_text(json.dumps([{**r, 'parsed_blocks':sum(b['source']==r['source'] and b['paper']==r['paper'] for b in corpus['blocks']), **({'path':Path(r['path']).name} if 'path' in r else {})} for r in corpus['receipts']],indent=2))
    versions={p:importlib.metadata.version(p) for p in ('numpy','torch','sentence-transformers','transformers','beautifulsoup4','langchain-text-splitters')}
    (args.output/'environment.json').write_text(json.dumps(versions,indent=2))
    print('\n'.join(lines[:22]))


if __name__=='__main__':
    main()
