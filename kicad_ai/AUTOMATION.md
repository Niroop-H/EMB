# EMB automation over native KiCad

This is a desktop companion to KiCad, not a replacement editor. KiCad's C++ UI,
engines, symbol/footprint libraries and file associations remain unchanged.
The companion opens `kicad`, `eeschema`, and `pcbnew` as installed applications.
No browser server, cloud key or new CAD rendering engine is needed.

## Run

Install KiCad with its official symbol, footprint and 3D libraries. Use a KiCad
version that supports your files. Python 3.10+ with Tkinter is needed when running
from source (the official Windows Python installer includes Tkinter).

From the repository root:

```sh
python -m kicad_ai.automation.desktop
```

On Windows, `LAUNCH_MAH_QUANTUM_STUDIO.bat` opens the same companion. If KiCad is
not on PATH, set `KICAD_BIN_DIR` to its installed `bin` folder. This override has
priority; an invalid override is reported instead of silently picking another version.

1. Open a native `.kicad_pro` project or copy a reviewed native template into a
   new directory. The original template is not overwritten. Use a self-contained
   project folder containing all hierarchical sheets and project-local resources.
2. Answer the system-function, power, interface, controller, mechanical,
   fabrication and environment questions. Save the brief and open native KiCad.
3. Implement/adapt the circuit using real KiCad symbols and footprints. Resolve
   every undecided requirement. Refill copper zones and save all editors.
4. Complete the named engineering review against datasheets and fabrication
   requirements. This records a hash of the saved project and brief.
5. Click **Final verification / FAB**. Do not edit the project while checks run.
6. Open the report. Print it and the linked pin diagrams through Print / Save PDF.

## Release policy

The workflow executes native ERC and DRC, including schematic/PCB parity and all
reported severities. Nested schematic sheets are included. Errors, warnings,
excluded violations, missing executables, unsupported file formats, failed
exports, malformed/missing reports and changed files all block release. Old clean
reports cannot be reused. A review becomes stale when the project or brief changes.
KiCad checks disabled in project settings remain a named engineering review item;
this tool does not silently change those settings.

Each run has a unique `.emb/runs/<id>/` directory containing:

- Fresh native JSON check results and a printable HTML report.
- Native schematic PDF and PCB assembly PDF, when export succeeds.
- A KiCad XML netlist, CSV of all library-defined pins, and printable logical pin
  connectivity diagrams, including pins with no exported net. These diagrams are
  not physical package drawings; package orientation requires the datasheet.
- Only after the checks and review pass: native BOM, actual PCB placement CSV,
  Gerbers and Excellon drill files. There are no hardcoded component coordinates
  or invented supplier part numbers.
- A manifest with source/artifact SHA-256 hashes and the KiCad version.

`MANUFACTURING_READY` means the recorded checks, required exports and named
engineering review passed for those exact saved files. It is not a promise of
functional correctness, an IPC certification, regulatory approval, or a
fabricator's DFM acceptance. Run the fabricator's checks before ordering.
Unsaved editor changes are not verified. Old reports are historical evidence,
not a live status for a subsequently changed project.

## What is and is not automated

Implemented: requirement capture, native template copy, native editor launch,
ERC/DRC execution, fabrication gating, native exports and pin documentation.

Not implemented: a validated general-purpose natural-language circuit designer,
auto-placement/autorouting, firmware synthesis or automatic datasheet reasoning.
The old heuristic pipelines invented partial footprints and cannot be trusted.
Their public generation entry points and legacy certificate generator are now
blocked. The former browser studio now launches this desktop companion. The
unused C++ copilot no longer prints fabricated success messages.

Files in `generated_systems/` and `sample_project/`, and their historical
certificates, are legacy demonstration artifacts, not approved manufacturing
releases. Do not order boards from those certificates. The sample uses a newer
file version than the KiCad 9.0.2 available in the development test environment.

## Command line and tests

```sh
python -m kicad_ai.run_foundry --questions
python -m kicad_ai.run_foundry --project /path/board.kicad_pro --requirements answers.json
python -m unittest discover -s kicad_ai/tests/automation -v
```

CLI exit status is 0 only for a ready release, or for `--questions`; blocked
verification exits 2. Record the named engineering review in the desktop UI.
Regression tests use synthetic CLI responses to exercise failures and the gated
success path; these are not hardware validation tests.

## Windows EXE / MSI packaging

The standalone packaging scripts package the companion, not a modified KiCad.
On Windows install Python, PyInstaller, CMake and the NSIS/WiX toolchain supported
by your CPack version, then run:

```powershell
.\kicad_ai\packaging\package_installer.ps1 -TargetInstaller ALL
```

The script builds the application, checks subprocess failures, and invokes
CPack to produce installers. It does not overwrite KiCad or claim to bundle
libraries it has not copied. KiCad plus its official libraries must be installed
separately. Windows packaging and installation still require testing on a Windows
VM; no Windows installer was built in the Linux development environment.

## Rule-based agent (current default)

The active assistant is a deterministic requirements workflow. It requires no
model, GPU, API key, inference server or Internet connection. The previous local
model adapter remains experimental source code and is not called by the desktop
assistant or legacy hardware-agent entry point. No BitNet integration is active.

Click **Ask rule-based agent**. Missing base answers and unresolved entries such
as TBD or unknown remain blocked. Explicit keywords in the function/interface
fields trigger additional questions for motors, batteries, radios, USB, analog
inputs and communication buses. Mixed systems receive every matching question
set. The technical-details form is scrollable and previously answered details
can be edited. Save the brief to persist the answers with the project.

All required questions must be answered before saving a brief or recording its
engineering review. Answers affect the review digest, so changing them requires
review again. These checks establish presence of information, not its engineering
correctness: rules do not reliably understand arbitrary natural language or
validate the numerical design. A named engineering review remains mandatory.

The deterministic states are NEEDS_ANSWERS and READY_FOR_TEMPLATE_REVIEW. Neither
state indicates fabrication readiness. There is no default ESP32 design and no
automatic circuit generation. Even an unrecognized system remains in the native
project/template workflow; it is never converted to a guessed topology.

Next work for bounded automatic generation is a separately validated template
catalog with explicit parameter limits, actual KiCad symbols/footprints and
pin mappings. No template has yet been qualified for automatic circuit synthesis.
Only Final verification / FAB can issue the existing gated release result.

The application has no active cloud calls. Deployment-level network isolation
still belongs to the operating system: KiCad, report viewers and other installed
software are separate components. Windows GUI/installers and security
accreditation remain untested in this development environment.
