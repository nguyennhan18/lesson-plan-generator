#!/usr/bin/env python3
"""Produce a review inventory without modifying sources or inventing approvals."""
import argparse,json
from pathlib import Path
from lessonai.rag.retriever import Math12HybridRetriever
from lessonai.rag.content_units import unit, asset_manifest
from lessonai.services.deck_lint import lint_slide


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    retriever=Math12HybridRetriever.get_instance()
    entries=[]
    for source_type,items in [('slide_kntt12',retriever.slides),('question_bank_rag',retriever.questions)]:
        for item in items:
            entry=unit(item,source_type)
            entry.update(status='needs_review',reviewer=None,reviewed_at=None)
            entry['structural_issues']=lint_slide(item,is_ingested_raw=True).get('errors',[]) if source_type=='slide_kntt12' else []
            try:
                entry['asset_hashes'] = asset_manifest(item)
            except (OSError, ValueError, TypeError) as error:
                entry['asset_issue'] = str(error)
            entries.append(entry)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump({'sources':entries,'notice':'Lint sạch không chứng nhận đúng toán. Cần đối chiếu nguồn và giáo viên duyệt từng hash.'},stream,ensure_ascii=False,indent=2)
    print(json.dumps({'units':len(entries),'approved':0,'output':str(path)}))

if __name__=='__main__':main()
