"""Keep source units whole. Only an explicit, hash-matched review enables reuse."""
import base64
import copy
import hashlib
import json
from lessonai.core.config import DATA_DIR


def source_snapshot(item):
    return {key:value for key,value in item.items() if key not in {'tokens','quality_score','retrieval_score'}}


def source_hash(item):
    return hashlib.sha256(json.dumps(source_snapshot(item),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def asset_manifest(item):
    """Fingerprint referenced assets too; unavailable/opaque references quarantine the unit."""
    manifest = {}
    for field in ('images', 'assets', 'media'):
        values = item.get(field) or []
        if not isinstance(values, list):
            raise ValueError('Danh sách asset không hợp lệ')
        for index, value in enumerate(values):
            reference = value if isinstance(value, str) else value.get('path') or value.get('source_part') or value.get('data_url') if isinstance(value, dict) else None
            inline = value.get('data_base64') if isinstance(value, dict) else None
            if inline:
                raw = base64.b64decode(inline, validate=True)
            elif isinstance(reference, str) and reference.startswith('data:image/'):
                raw = base64.b64decode(reference.split(',', 1)[1], validate=True)
            elif reference:
                path = (DATA_DIR / reference).resolve()
                if not path.is_relative_to(DATA_DIR.resolve()) or not path.is_file():
                    raise ValueError('Asset thiếu hoặc nằm ngoài kho dữ liệu')
                raw = path.read_bytes()
            else:
                raise ValueError('Asset chưa có dữ liệu để đối chiếu')
            manifest[f'{field}[{index}]'] = hashlib.sha256(raw).hexdigest()
    return manifest


def approved_units(items):
    path = DATA_DIR / 'reviewed_sources.json'
    try:
        registry = json.loads(path.read_text())
        records = registry.get('sources', []) if isinstance(registry, dict) else []
        if not isinstance(records, list):
            return []
        approved = {record['sha256']: record for record in records if isinstance(record, dict) and record.get('status') == 'approved' and record.get('reviewer') and record.get('reviewed_at')}
    except (OSError, ValueError, KeyError, TypeError):
        return []
    result = []
    for item in items:
        record = approved.get(source_hash(item))
        if record is None:
            continue
        try:
            if asset_manifest(item) != record.get('asset_hashes', {}):
                continue
        except (OSError, ValueError, TypeError):
            continue
        result.append(copy.deepcopy(item))
    return result


def unit(item,source_type):
    raw=source_snapshot(item)
    return {'source_type':source_type,'id':item.get('slide_id') or item.get('id') or item.get('question_id'),
            'sha256':source_hash(item),'content':raw}
