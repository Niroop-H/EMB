# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic intake rules. These rules never synthesize or approve a circuit."""
import re

RULES = (
    ('motor', r'\b(motor|stepper|servo|actuator)s?\b', (
        ('motor_load', 'Specify motor voltage, running/stall current and number of channels.'),
        ('motor_protection', 'Specify driver interface, flyback protection and emergency-stop behavior.'),
    )),
    ('battery', r'\b(battery|batteries|lipo|li-ion|charging|charger)\b', (
        ('battery_pack', 'Specify chemistry, series cell count, capacity and charge/discharge limits.'),
        ('battery_protection', 'Specify charger, protection, temperature monitoring and power-path requirements.'),
    )),
    ('wireless', r'\b(wifi|wi-fi|bluetooth|ble|lora|rf|wireless)\b', (
        ('wireless_module', 'Specify radio/module variant, antenna arrangement and required operating region.'),
    )),
    ('usb', r'\busb(?:-c)?\b', (
        ('usb_role', 'Specify USB host/device role, data speed and connector type.'),
        ('usb_power', 'Specify USB power role, current limit, CC/PD requirements and ESD protection.'),
    )),
    ('analog', r'\b(adc|analog|analogue|precision)\b', (
        ('analog_input', 'Specify input range, bandwidth/sample rate, accuracy and reference requirements.'),
    )),
    ('bus', r'\b(can(?:-fd)?|rs-?485|i2c|spi)\b', (
        ('bus_electrical', 'Specify bus speeds, voltage levels, cable lengths, termination and isolation requirements.'),
    )),
)
UNRESOLVED = re.compile(r'\b(tbd|unknown|undecided|not sure|to be decided)\b', re.I)


def answered(value):
    return isinstance(value, str) and bool(value.strip()) and not UNRESOLVED.search(value)


class RuleAgent:
    def assess(self, answers):
        from .workflow import QUESTIONS
        if not isinstance(answers, dict):
            raise ValueError('Requirements must be an object')
        pending = [{'id': key, 'question': question, 'kind': 'base'}
                   for key, question in QUESTIONS.items() if not answered(answers.get(key))]
        # Only explicit function/interface fields activate categories. An unrelated
        # fabrication vendor or free-form response must not select a circuit template.
        text = ' '.join(answers.get(key, '') for key in ('function', 'interfaces')
                        if isinstance(answers.get(key), str)).lower()
        details = answers.get('details', {})
        if not isinstance(details, dict):
            raise ValueError('Requirement details must be an object')
        categories = []
        detail_fields = []
        for category, pattern, questions in RULES:
            if re.search(pattern, text):
                categories.append(category)
                detail_fields.extend({'id': key, 'question': question, 'kind': 'detail'} for key, question in questions)
                pending.extend({'id': key, 'question': question, 'kind': 'detail'}
                               for key, question in questions if not answered(details.get(key)))
        return {
            'state': 'NEEDS_ANSWERS' if pending else 'READY_FOR_TEMPLATE_REVIEW',
            'summary': ('Resolve the listed requirements before proceeding.' if pending else
                        'Intake is complete. Select and review a native KiCad template; no circuit has been generated or verified.'),
            'questions': [item['question'] for item in pending],
            'pending': pending,
            'detail_fields': detail_fields,
            'categories': categories,
            'manufacturing_ready': False,
            'generation_supported': False,
        }

    def questions(self, answers):
        return self.assess(answers)
