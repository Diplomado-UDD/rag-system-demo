## Why

Deleting an uploaded PDF currently fails from the user interface, producing an error dialog instead of removing the document. This breaks a basic document-management workflow and leaves users unable to clean up incorrect or obsolete uploads.

## What Changes

- Define the expected document-deletion behavior for the web application and API.
- Ensure successful deletion is treated as a success path in the frontend even when the API returns no response body.
- Tighten backend deletion semantics so document and chunk removal happen as one logical operation.
- Define error handling for deletion failures so users receive accurate feedback when a document cannot be removed.

## Capabilities

### New Capabilities
- `document-deletion`: Covers deleting an uploaded document, removing its associated chunks, and reporting success or failure consistently across the API and frontend.

### Modified Capabilities

## Impact

- Frontend document management in `frontend/src/services/api.js` and `frontend/src/components/DocumentList.jsx`.
- Backend deletion endpoint in `src/api/routes/documents.py`.
- Repository transaction behavior in `src/repositories/base.py` and `src/repositories/vector_repo.py`.
- Tests for document deletion behavior across frontend-facing API handling and backend repository or route semantics.