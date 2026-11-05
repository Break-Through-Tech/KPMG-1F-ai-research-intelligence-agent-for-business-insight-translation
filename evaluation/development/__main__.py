"""Validate local development inputs without retrieval or generation."""
import argparse,json
from pathlib import Path
from .validation import load_questions,aggregate_credits

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--questions',type=Path,default=Path(__file__).with_name('questions.json'))
    parser.add_argument('--reviews',type=Path,help='Optional private local point-credit JSON list; no automatic grading.')
    args=parser.parse_args();cases=load_questions(args.questions)
    if args.reviews:
        reviews=json.loads(args.reviews.read_text(encoding='utf-8'))
        print(json.dumps(aggregate_credits(cases,reviews),indent=2))
    else:print(json.dumps({'development_questions':len(cases),'answerable':sum(c['required_points_count']>0 for c in cases),'answer_keys_included':False,'generation_calls':0}))
if __name__=='__main__':main()
