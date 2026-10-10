import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from issues.models import CriticalIssue, Issue, LowPriorityIssue, Reporter
from issues.storage import (
    find_by_id,
    load_issues,
    load_reporters,
    save_issues,
    save_reporters,
)


def _parse_json_body(request):
    if not request.body:
        raise ValueError('Request body cannot be empty')
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ValueError('Invalid JSON') from exc
    if not isinstance(data, dict):
        raise ValueError('JSON body must be an object')
    return data


def _as_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} must be an integer') from exc


def _build_issue(data):
    fields = {
        'id': _as_int(data['id'], 'id'),
        'title': data.get('title', ''),
        'description': data.get('description', ''),
        'status': data.get('status', ''),
        'priority': data.get('priority', ''),
        'reporter_id': _as_int(data['reporter_id'], 'reporter_id'),
    }
    if data.get('priority') == 'critical':
        return CriticalIssue(**fields)
    if data.get('priority') == 'low':
        return LowPriorityIssue(**fields)
    return Issue(**fields)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def reporters(request):
    if request.method == 'POST':
        try:
            data = _parse_json_body(request)
            reporter = Reporter(
                id=_as_int(data['id'], 'id'),
                name=data.get('name', ''),
                email=data.get('email', ''),
                team=data.get('team', ''),
            )
            reporter.validate()
        except KeyError as exc:
            return JsonResponse({'error': f'Missing field: {exc.args[0]}'}, status=400)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        records = load_reporters()
        if find_by_id(records, reporter.id):
            return JsonResponse({'error': 'Reporter with this id already exists'}, status=400)

        records.append(reporter.to_dict())
        save_reporters(records)
        return JsonResponse(reporter.to_dict(), status=201)

    reporter_id = request.GET.get('id')
    records = load_reporters()

    if reporter_id is not None:
        try:
            reporter_id = int(reporter_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'id must be an integer'}, status=400)

        reporter = find_by_id(records, reporter_id)
        if reporter is None:
            return JsonResponse({'error': 'Reporter not found'}, status=404)
        return JsonResponse(reporter, status=200)

    return JsonResponse(records, safe=False, status=200)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def issues(request):
    if request.method == 'POST':
        try:
            data = _parse_json_body(request)
            if 'id' not in data or 'reporter_id' not in data:
                missing = 'id' if 'id' not in data else 'reporter_id'
                return JsonResponse({'error': f'Missing field: {missing}'}, status=400)

            issue = _build_issue(data)
            reporters = load_reporters()
            if find_by_id(reporters, issue.reporter_id) is None:
                return JsonResponse({'error': 'Reporter not found'}, status=404)

            issue.validate()
        except KeyError as exc:
            return JsonResponse({'error': f'Missing field: {exc.args[0]}'}, status=400)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        records = load_issues()
        if find_by_id(records, issue.id):
            return JsonResponse({'error': 'Issue with this id already exists'}, status=400)

        records.append(issue.to_dict())
        save_issues(records)

        response_data = issue.to_dict()
        response_data['message'] = issue.describe()
        return JsonResponse(response_data, status=201)

    records = load_issues()
    issue_id = request.GET.get('id')
    status_filter = request.GET.get('status')

    if issue_id is not None:
        try:
            issue_id = int(issue_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'id must be an integer'}, status=400)

        issue = find_by_id(records, issue_id)
        if issue is None:
            return JsonResponse({'error': 'Issue not found'}, status=404)
        return JsonResponse(issue, status=200)

    if status_filter is not None:
        filtered = [issue for issue in records if issue.get('status') == status_filter]
        return JsonResponse(filtered, safe=False, status=200)

    return JsonResponse(records, safe=False, status=200)
