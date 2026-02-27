## Context

The `select_quality_and_language` function in `quality_selector.py` filters quality options by episode when specified. Currently, if the filter returns no options, it returns `None` silently, and the caller displays a generic "No quality selected" error.

## Goals / Non-Goals

**Goals:**
- Display a clear error message when no quality options exist for the selected episode

**Non-Goals:**
- Change the quality selection flow logic
- Modify how episodes without options are handled beyond error messaging

## Decisions

### Decision 1: Error handling approach

Instead of returning `None` from `select_quality_and_language` when filtering yields empty results, we should print a descriptive error message and return `None`. This keeps the function's contract consistent (still returns `Optional[QualityOption]`) while providing better feedback.

The error message should be: available for episode { "No quality optionsepisode}"

### Decision 2: Implementation location

The change belongs in `select_quality_and_language` at line 112-113 where the empty check occurs. We need access to the episode parameter, which is already available in scope.
