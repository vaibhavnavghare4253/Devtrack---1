import json
from pathlib import Path

from django.conf import settings

REPORTERS_FILE = Path(settings.BASE_DIR) / 'reporters.json'
ISSUES_FILE = Path(settings.BASE_DIR) / 'issues.json'


def _ensure_file(path):
    if not path.exists():
        path.write_text('[]', encoding='utf-8')


def load_records(path):
    _ensure_file(path)
    with open(path, 'r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        return []
    return data


def save_records(path, records):
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(records, handle, indent=2)


def load_reporters():
    return load_records(REPORTERS_FILE)


def save_reporters(records):
    save_records(REPORTERS_FILE, records)


def load_issues():
    return load_records(ISSUES_FILE)


def save_issues(records):
    save_records(ISSUES_FILE, records)


def find_by_id(records, record_id):
    for record in records:
        if record.get('id') == record_id:
            return record
    return None
