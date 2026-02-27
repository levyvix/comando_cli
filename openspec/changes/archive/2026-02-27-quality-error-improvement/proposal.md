## Why

When users select a specific episode for a series, the quality selection fails silently if no quality options match that episode. The error message shows "No quality selected" which is confusing—it should clearly indicate no options exist for the selected episode.

## What Changes

- Better error message in `select_quality_and_language` when episode filtering returns no options

## Capabilities

### Modified Capabilities
- `select_quality_and_language`: SHALL show helpful error when no quality options exist for selected episode

## Impact

- `src/comando_cli/quality_selector.py`: Add descriptive error message in empty quality options case
