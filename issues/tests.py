import json
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings


@override_settings(
    BASE_DIR=settings.BASE_DIR,
)
class ApiTests(TestCase):
    def setUp(self):
        self.reporters_path = Path(settings.BASE_DIR) / 'reporters.json'
        self.issues_path = Path(settings.BASE_DIR) / 'issues.json'
        self.reporters_backup = self.reporters_path.read_text(encoding='utf-8') if self.reporters_path.exists() else '[]'
        self.issues_backup = self.issues_path.read_text(encoding='utf-8') if self.issues_path.exists() else '[]'
        self.reporters_path.write_text('[]', encoding='utf-8')
        self.issues_path.write_text('[]', encoding='utf-8')

    def tearDown(self):
        self.reporters_path.write_text(self.reporters_backup, encoding='utf-8')
        self.issues_path.write_text(self.issues_backup, encoding='utf-8')

    def test_create_reporter_and_critical_issue(self):
        reporter_response = self.client.post(
            '/api/reporters/',
            data=json.dumps({
                'id': 1,
                'name': 'Asha Patel',
                'email': 'asha@example.com',
                'team': 'backend',
            }),
            content_type='application/json',
        )
        self.assertEqual(reporter_response.status_code, 201)

        issue_response = self.client.post(
            '/api/issues/',
            data=json.dumps({
                'id': 1,
                'title': 'Login button not working on mobile',
                'description': 'Users on iOS 17 cannot tap the login button',
                'status': 'open',
                'priority': 'critical',
                'reporter_id': 1,
            }),
            content_type='application/json',
        )
        self.assertEqual(issue_response.status_code, 201)
        payload = issue_response.json()
        self.assertEqual(
            payload['message'],
            '[URGENT] Login button not working on mobile — needs immediate attention',
        )

    def test_empty_title_returns_400(self):
        self.client.post(
            '/api/reporters/',
            data=json.dumps({
                'id': 1,
                'name': 'Asha Patel',
                'email': 'asha@example.com',
                'team': 'backend',
            }),
            content_type='application/json',
        )
        response = self.client.post(
            '/api/issues/',
            data=json.dumps({
                'id': 1,
                'title': '',
                'description': 'Missing title',
                'status': 'open',
                'priority': 'high',
                'reporter_id': 1,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Title cannot be empty'})

    def test_missing_issue_returns_404(self):
        response = self.client.get('/api/issues/?id=999')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Issue not found'})
