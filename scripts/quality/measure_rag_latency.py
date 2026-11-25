"""Read-only corpus benchmark; approvals live in a temporary directory."""
import json
import statistics
import tempfile
import time
from pathlib import Path
from lessonai.rag import content_units as cu
from lessonai.rag.retriever import Math12HybridRetriever

LESSONS = ('M12-C1-B1', 'M12-C2-B2', 'M12-C3-B1', 'M12-C3-B2', 'M12-C5-B1')


def main():
    r = Math12HybridRetriever()
    with tempfile.TemporaryDirectory(prefix='rag-perf-approvals-') as temp:
        cu.DATA_DIR = Path(temp)
        records = []
        for kind, items in [('slide_kntt12', r._slides), ('question_bank_rag', r._questions)]:
            for item in items:
                if item.get('lesson_id') not in LESSONS:
                    continue
                try:
                    assets = cu.asset_manifest(item)
                except ValueError:
                    continue
                records.append(dict(source_id=item.get('id') or item.get('slide_id'), source_type=kind,
                    document_version=item.get('document_version') or item.get('version') or 'unknown',
                    status='approved', sha256=cu.source_hash(item), hash_version=getattr(cu, 'HASH_VERSION', 1),
                    reviewer='TEST ONLY', reviewed_at='2026-11-14T00:00:00Z', asset_hashes=assets))
        cu.save_approval_registry({'schema_version': 1, 'sources': records})
        samples = {lid: [] for lid in LESSONS}
        for _ in range(20):
            for lid in LESSONS:
                start = time.perf_counter_ns()
                r.retrieve_lesson_skeleton(lid)
                slides = r.retrieve_exemplar_slides(lid, activity_type='luyen_tap', query='bài tập ví dụ', k=2)
                questions = r.retrieve_questions(lid, proficiency='standard', query='tính toán', k=3)
                samples[lid].append((time.perf_counter_ns() - start) / 1e6)
                assert slides and questions
        print(json.dumps({lid: {'min': min(s), 'median': statistics.median(s), 'max': max(s), 'samples_ms': s} for lid, s in samples.items()}))


if __name__ == '__main__':
    main()
