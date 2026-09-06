## Problem

Development artifacts were committed to the repository:
- `app/img/test_labels.png` (243KB)
- `app/img/test_labels2.png` (232KB)
- `app/img/test_select_star.png` (239KB)

These are temporary screenshots created during development and are not referenced in the README or anywhere else in the project.

## Impact

- Bloated repository size (+714KB of dead weight)
- Unprofessional appearance — looks like a work-in-progress
- Sets a bad example for contributors

## Fix

1. Remove the three test screenshot files
2. Add `app/img/test_*.png` to `.gitignore` to prevent recurrence

## Acceptance Criteria

- [ ] `app/img/test_labels.png` removed from git
- [ ] `app/img/test_labels2.png` removed from git
- [ ] `app/img/test_select_star.png` removed from git
- [ ] `.gitignore` updated with `app/img/test_*.png`
- [ ] README screenshots (`screenshot_*.png`) are preserved
