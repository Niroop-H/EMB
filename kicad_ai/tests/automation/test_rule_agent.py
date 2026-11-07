# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import patch
from kicad_ai.automation.rule_agent import RuleAgent
from kicad_ai.automation.workflow import QUESTIONS, missing_questions


class RuleAgentTests(unittest.TestCase):
    def setUp(self):
        self.answers = {key: 'Reviewed specific requirement' for key in QUESTIONS}
        self.agent = RuleAgent()

    def test_missing_or_undecided_answers_block(self):
        for value in ('', 'TBD', 'controller undecided', 'unknown'):
            data = {**self.answers, 'controller': value}
            self.assertIn('controller', missing_questions(data))
            self.assertEqual(self.agent.assess(data)['state'], 'NEEDS_ANSWERS')

    def test_mixed_system_questions_and_answers(self):
        data = {**self.answers, 'function': 'Battery powered servo controller with USB-C and Wi-Fi'}
        result = self.agent.assess(data)
        self.assertEqual(set(result['categories']), {'battery', 'motor', 'usb', 'wireless'})
        data['details'] = {q['id']: 'Specific design requirement' for q in result['pending']}
        result = self.agent.assess(data)
        self.assertEqual(result['state'], 'READY_FOR_TEMPLATE_REVIEW')
        self.assertFalse(result['manufacturing_ready'])
        data['details']['motor_load'] = 'TBD'
        self.assertIn('motor_load', missing_questions(data))

    def test_no_keyword_default_circuit(self):
        result = self.agent.assess({**self.answers, 'function': 'Unrecognized custom system'})
        self.assertEqual(result['categories'], [])
        self.assertFalse(result['generation_supported'])
        self.assertNotIn('components', result)

    def test_deterministic_and_no_network_or_model(self):
        with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
            with patch('kicad_ai.automation.local_model.LocalModel.load', side_effect=AssertionError('model forbidden')):
                self.assertEqual(self.agent.assess(self.answers), self.agent.assess(self.answers))

    def test_keyword_boundaries(self):
        result = self.agent.assess({**self.answers, 'function': 'Canopy measurement device'})
        self.assertNotIn('bus', result['categories'])

    def test_invalid_details_rejected(self):
        with self.assertRaises(ValueError):
            self.agent.assess({**self.answers, 'details': []})
