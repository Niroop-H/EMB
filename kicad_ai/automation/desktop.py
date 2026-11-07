# SPDX-License-Identifier: GPL-3.0-or-later
"""Small desktop companion; KiCad owns every schematic and PCB editing surface."""
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

from .rule_agent import RuleAgent
from .native import open_editor
from .release import verify_fabrication
from .workflow import (QUESTIONS, REVIEW_ITEMS, project_path, save_brief, brief_path,
                       record_review, copy_template)


class Companion:
    def __init__(self, root):
        self.root = root
        self.project = None
        self.report = None
        self.events = queue.Queue()
        self.busy = False
        self.rule_agent = RuleAgent()
        self.details = {}
        root.title('EMB — KiCad Automation')
        root.geometry('850x760')
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='KiCad Automation', font=('', 18)).pack(anchor='w')
        ttk.Label(frame, text='Describe the system, review the requirements, then work in the original KiCad editors.',
                  wraplength=790).pack(anchor='w', pady=8)
        controls = ttk.Frame(frame)
        controls.pack(fill='x')
        ttk.Button(controls, text='Open project', command=self.select_project).pack(side='left')
        ttk.Button(controls, text='Copy native template', command=self.select_template).pack(side='left', padx=8)
        self.project_label = ttk.Label(frame, text='No project selected', wraplength=790)
        self.project_label.pack(anchor='w', pady=8)
        notebook = ttk.Notebook(frame)
        notebook.pack(fill='both', expand=True)
        intake, review = ttk.Frame(notebook, padding=10), ttk.Frame(notebook, padding=10)
        notebook.add(intake, text='Requirements')
        notebook.add(review, text='Engineering review')
        self.answers = {}
        for key, question in QUESTIONS.items():
            ttk.Label(intake, text=question, wraplength=760).pack(anchor='w')
            entry = ttk.Entry(intake)
            entry.pack(fill='x', pady=(3, 10))
            self.answers[key] = entry
        ttk.Button(intake, text='Ask rule-based agent', command=self.ask_agent).pack(anchor='w', pady=4)
        ttk.Button(intake, text='Save requirements and open KiCad', command=self.proceed).pack(anchor='w')
        ttk.Label(intake, text='This version uses a selected native project/template. It does not synthesize arbitrary circuits. '
                  'Resolve undecided requirements and edit the design in KiCad before release.',
                  wraplength=750).pack(anchor='w', pady=8)
        ttk.Label(review, text='Review this saved design against its requirements and exact datasheets.',
                  wraplength=750).pack(anchor='w', pady=8)
        self.checks = {}
        for item in REVIEW_ITEMS:
            variable = tk.BooleanVar()
            self.checks[item] = variable
            row = ttk.Frame(review)
            row.pack(fill='x', pady=8)
            ttk.Checkbutton(row, variable=variable).pack(side='left')
            ttk.Label(row, text=item, wraplength=700).pack(side='left')
        ttk.Label(review, text='Reviewer name').pack(anchor='w')
        self.reviewer = ttk.Entry(review)
        self.reviewer.pack(fill='x')
        ttk.Button(review, text='Record review of saved files', command=self.review).pack(anchor='w', pady=12)
        bar = ttk.Frame(frame)
        bar.pack(fill='x', pady=12)
        for text, editor in [('KiCad project', 'kicad'), ('Schematic', 'eeschema'), ('PCB', 'pcbnew')]:
            ttk.Button(bar, text=text, command=lambda e=editor: self.open_native(e)).pack(side='left', padx=3)
        self.verify_button = ttk.Button(bar, text='Final verification / FAB', command=self.verify)
        self.verify_button.pack(side='right')
        self.report_button = ttk.Button(frame, text='Open printable report and pin diagrams',
                                        command=self.open_report, state='disabled')
        self.report_button.pack(anchor='w')
        self.status = ttk.Label(frame, text='Ready. Save all KiCad files before verification.', wraplength=790)
        self.status.pack(anchor='w', pady=10)
        root.after(100, self.poll)

    def error(self, exc):
        messagebox.showerror('KiCad Automation', str(exc), parent=self.root)

    def set_project(self, value):
        if self.busy:
            raise ValueError('Wait for verification to finish before changing projects')
        self.project = project_path(value)
        self.project_label.configure(text=str(self.project))
        self.report = None
        self.report_button.configure(state='disabled')
        for variable in self.checks.values():
            variable.set(False)
        self.reviewer.delete(0, 'end')
        data = {}
        if brief_path(self.project).exists():
            data = json.loads(brief_path(self.project).read_text(encoding='utf-8'))
        self.details = data.get('details', {})
        for key, entry in self.answers.items():
            entry.delete(0, 'end')
            entry.insert(0, data.get(key, ''))

    def select_project(self):
        if self.busy:
            return
        value = filedialog.askopenfilename(filetypes=[('KiCad project', '*.kicad_pro')])
        if value:
            try:
                self.set_project(value)
            except Exception as exc:
                self.error(exc)

    def select_template(self):
        if self.busy:
            return
        source = filedialog.askopenfilename(title='Select a reviewed native KiCad template',
                                            filetypes=[('KiCad project', '*.kicad_pro')])
        if not source:
            return
        target = filedialog.asksaveasfilename(title='New project folder (must not exist)', filetypes=[])
        if target:
            try:
                self.set_project(copy_template(source, target))
            except Exception as exc:
                self.error(exc)

    def require_project(self):
        if not self.project:
            raise ValueError('Open or copy a KiCad project first')
        if self.busy:
            raise ValueError('Verification is running; wait for the result')

    def save_answers(self):
        save_brief(self.project, {**{key: entry.get() for key, entry in self.answers.items()}, 'details': dict(self.details)})

    def proceed(self):
        try:
            self.require_project()
            self.save_answers()
            open_editor(self.project)
            self.status.configure(text='Requirements saved. Implement and review the design in KiCad; verification remains required.')
        except Exception as exc:
            self.error(exc)

    def review(self):
        try:
            self.require_project()
            self.save_answers()
            record_review(self.project, self.reviewer.get(),
                          [key for key, variable in self.checks.items() if variable.get()])
            self.status.configure(text='Review recorded for current saved files. Final verification is still required.')
        except Exception as exc:
            self.error(exc)

    def open_native(self, editor):
        try:
            self.require_project()
            open_editor(self.project, editor)
        except Exception as exc:
            self.error(exc)

    def ask_agent(self):
        if self.busy:
            return
        answers = {**{key: entry.get() for key, entry in self.answers.items()},
                   'details': dict(self.details)}
        result = self.rule_agent.assess(answers)
        self.status.configure(text=result['summary'])
        detail_questions = result['detail_fields']
        if not detail_questions:
            messagebox.showinfo('Rule-based requirements assistant', result['summary'] + '\n\n' +
                                '\n'.join(result['questions']), parent=self.root)
            return
        window = tk.Toplevel(self.root)
        window.title('Required engineering details')
        window.transient(self.root)
        window.grab_set()
        # Scrollable form supports mixed-category systems without hiding questions.
        canvas = tk.Canvas(window, width=760, height=500)
        scroll = ttk.Scrollbar(window, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        form = ttk.Frame(canvas, padding=12)
        canvas.create_window((0, 0), window=form, anchor='nw')
        form.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        fields = {}
        for item in detail_questions:
            ttk.Label(form, text=item['question'], wraplength=700).pack(anchor='w', pady=(8, 2))
            entry = ttk.Entry(form, width=90)
            entry.insert(0, self.details.get(item['id'], ''))
            entry.pack(fill='x')
            fields[item['id']] = entry
        def accept():
            self.details.update({key: entry.get().strip() for key, entry in fields.items()})
            window.destroy()
            self.status.configure(text='Details captured. Ask the agent again to check remaining questions, then save requirements.')
        ttk.Button(form, text='Keep answers', command=accept).pack(anchor='w', pady=12)

    def verify(self):
        try:
            self.require_project()
            self.save_answers()
        except Exception as exc:
            self.error(exc)
            return
        self.busy = True
        self.report = None
        self.report_button.configure(state='disabled')
        self.verify_button.configure(state='disabled')
        self.status.configure(text='Running native KiCad checks and exports. Keep the project unchanged until this finishes.')
        project = self.project
        def worker():
            try:
                self.events.put(('result', verify_fabrication(project)))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            kind, payload = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.verify_button.configure(state='normal')
            if kind == 'error':
                self.status.configure(text='Verification failed; no manufacturing-ready release issued.')
                self.error(payload)
            else:
                result, self.report = payload
                self.report_button.configure(state='normal')
                self.status.configure(text=('Manufacturing-ready document is listed for the verified saved files.'
                    if result['manufacturing_ready'] else 'BLOCKED: ' + '; '.join(result['blockers'])))
                self.open_report()
        self.root.after(100, self.poll)

    def open_report(self):
        if self.report:
            webbrowser.open(self.report.as_uri())


def main():
    root = tk.Tk()
    Companion(root)
    root.mainloop()


if __name__ == '__main__':
    main()
