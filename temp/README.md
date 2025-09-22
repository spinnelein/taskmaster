# Temporary Files Directory

This directory contains temporary test files and experimental code that should not be part of the main codebase.

## Directory Structure

- `yolo_tests/` - YOLO system integration test files
  - All Unicode characters have been cleaned (ASCII-only)
  - Files moved here per CODING_STANDARDS.md requirements
  - These are temporary test files for development validation

## Cleanup Policy

Files in this directory should be:
- Reviewed periodically and removed when no longer needed
- Not committed to the main codebase
- Kept separate from production code

## Current Status

- **Unicode Violation Fix**: All YOLO test files cleaned of Unicode characters (✅→PASS, ❌→FAIL, ⚠️→WARNING, 🎉→SUCCESS)
- **File Organization**: Moved from root directory per CODING_STANDARDS.md Section 2
- **Windows Console Compatibility**: All files now work with cp1252 encoding