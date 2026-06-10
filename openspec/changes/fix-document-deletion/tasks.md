## 1. Reproduce And Cover The Failure

- [x] 1.1 Add a focused test that reproduces the frontend failure when `DELETE /documents/{id}` returns `204 No Content` without a JSON body.
- [x] 1.2 Add or update backend deletion tests to cover successful document removal and accurate failure reporting for a missing document.

## 2. Fix Frontend Delete Success Handling

- [x] 2.1 Update the shared frontend request helper so successful empty-body responses are handled without JSON parsing errors.
- [x] 2.2 Verify the document list delete flow removes the item and clears the selected filter when the deleted document was active.

## 3. Make Backend Deletion Atomic

- [x] 3.1 Refactor repository or route delete behavior so chunk deletion and document deletion share one transaction boundary.
- [x] 3.2 Ensure backend deletion errors preserve a consistent state instead of partially deleting related data.

## 4. Validate End-To-End Behavior

- [x] 4.1 Run focused unit and integration tests for the touched frontend and backend deletion paths.
- [x] 4.2 Behavior-validate document deletion through the running application or API and confirm the document disappears without the current error dialog.