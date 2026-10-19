"""Behavior checks for safe, non-executing multi-actor planning and redaction."""
import json
from pathlib import Path
import tempfile
import unittest

import plan_sessions
import probe_wechat


CANDIDATE = 'a' * 40


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.install = self.root / 'ide'
        self.install.mkdir()
        (self.install / 'cli.bat').write_text('placeholder', encoding='utf-8')
        self.projects = []
        for name in ('a', 'b'):
            project = self.root / name
            project.mkdir()
            (project / 'project.config.json').write_text('{}', encoding='utf-8')
            self.projects.append(project)
        self.config = {
            'candidate': CANDIDATE,
            'route': 'bridge-project',
            'actors': [
                {'alias': 'player-a', 'project': str(self.projects[0]), 'port': 9421, 'accountEnv': 'WX_A'},
                {'alias': 'player-b', 'project': str(self.projects[1]), 'port': 9422, 'accountEnv': 'WX_B'},
            ],
        }

    def test_plan_does_not_export_account_values_or_claim_routing(self):
        secret_a, secret_b = 'sensitive-account-alpha', 'sensitive-account-beta'
        result = plan_sessions.plan(self.config, self.install, {'WX_A': secret_a, 'WX_B': secret_b})
        serialized = json.dumps(result)
        self.assertNotIn(secret_a, serialized)
        self.assertNotIn(secret_b, serialized)
        self.assertFalse(result['executed'])
        self.assertTrue(all(not actor['routingVerified'] for actor in result['actors']))
        self.assertTrue(all(actor['accountConfigured'] for actor in result['actors']))

    def test_duplicate_account_port_and_project_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'account'):
            plan_sessions.plan(self.config, self.install, {'WX_A': 'same', 'WX_B': 'same'})
        self.config['actors'][1]['port'] = 9421
        with self.assertRaisesRegex(ValueError, 'port'):
            plan_sessions.plan(self.config, self.install, {})
        self.config['actors'][1]['port'] = 9422
        self.config['actors'][1]['project'] = str(self.projects[0])
        with self.assertRaisesRegex(ValueError, 'project'):
            plan_sessions.plan(self.config, self.install, {})
        self.config['route'] = 'sdk-port'
        self.assertEqual(len(plan_sessions.plan(self.config, self.install, {})['actors']), 2)

    def test_candidate_and_install_must_be_real_inputs(self):
        self.config['candidate'] = 'replace-with-fixed-commit'
        with self.assertRaisesRegex(ValueError, 'fixed 40-character Git commit'):
            plan_sessions.plan(self.config, self.install, {})
        self.config['candidate'] = CANDIDATE
        (self.install / 'cli.bat').unlink()
        with self.assertRaisesRegex(ValueError, 'cli.bat'):
            plan_sessions.plan(self.config, self.install, {})

    def test_account_probe_reports_count_without_identity_data(self):
        reply = {'ok': True, 'result': {'success': True,
                                      'accounts': [{'openid': 'secret-one', 'ticket': 'secret-two'}]}}
        result = probe_wechat.summarize_accounts(reply)
        self.assertTrue(result['ok'])
        self.assertEqual(result['count'], 1)
        self.assertNotIn('secret-one', json.dumps(result))
        self.assertNotIn('secret-two', json.dumps(result))
        self.assertIn('not a count of open', result['interpretation'])


if __name__ == '__main__':
    unittest.main()
