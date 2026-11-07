# SPDX-License-Identifier: GPL-3.0-or-later
"""Legacy agent compatibility; model-backed hardware generation is disabled."""


class BaseHardwareAgent:
    def __init__(self, name, role_description, model='disabled'):
        self.name = name
        self.role_description = role_description
        self.model = model
        self.history = []
        self.system_prompt = role_description

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def call_llm(self, prompt, schema=None):
        from ..automation.local_model import LocalModelError
        raise LocalModelError('Model-backed generation is disabled. Use the deterministic requirements agent and a reviewed native KiCad template.')

    def synthesize_heuristic(self, prompt):
        raise NotImplementedError('Heuristic hardware generation is not an approved fallback')
