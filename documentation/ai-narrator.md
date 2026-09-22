# Free offline summary

The project uses a local template summary. No API key, credits or payment is required. Paid AI narration was skipped at the user’s request.

## Generate the summary

Double-click `Run AI Brief.cmd`. It runs `python src/generate_insights.py --preview` and makes no API request.

Open `outputs/sample_brief_preview.md`. The matching JSON and provenance files record the template output and source hashes.

## Scope and limitations

The summary uses validated aggregate metrics for July 2018 versus July 2017. It is an offline template, not AI-generated analysis or a current sales update. Figures have evidence references; causal explanations are not established.

The optional API implementation remains in the source for future development but is not used by the launcher. Previous live attempts did not generate a brief; the last API response reported no credits. Adding credits is not a remaining project requirement.
