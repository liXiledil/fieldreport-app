# Word import macro

`ImportFields.bas` loads a `<template>.fields.txt` file (written by `python -m fieldreport.cli`) into the open report template. It doesn't modify the template's own macros.

## One-time setup per template

1. Open the template (or a copy of it) and press **Alt+F11**. Choose **File > Import File...** and pick `ImportFields.bas`.
2. Mark where each section goes, using either:
   - a **Rich Text content control** (Developer tab; plain text controls hold only one paragraph) whose **Tag** is the field name from `template_section_map.json` (e.g. `summary`, `findings`), or
   - a **bookmark** with that name (Insert > Bookmark).
3. Save as macro-enabled (.docm/.dotm).

Get your template owner's okay before editing company templates.

## Each job

Open the report, run your normal macros, then run **ImportFieldReport** and pick the `.fields.txt` file. A message lists any field that had no matching control or bookmark.
