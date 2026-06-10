## Context

The current delete flow spans the React document list, a shared frontend request helper, the FastAPI delete route, and repository methods for documents and chunks. The route already returns `204 No Content`, which is a valid success response for deletion, but the shared frontend request helper always attempts to parse JSON and therefore converts a successful empty response into a client-side error. On the backend, chunk deletion and document deletion each commit independently, which creates a consistency gap if the second step fails after the first has already been committed.

## Goals / Non-Goals

**Goals:**
- Make document deletion succeed end to end when the API returns a successful empty response.
- Ensure document deletion removes both the document row and its related chunks as one logical operation.
- Preserve clear user feedback for real deletion failures such as missing documents or database errors.
- Add focused coverage for the success path and failure path of deletion behavior.

**Non-Goals:**
- Redesign the broader frontend API client abstraction beyond the response handling needed for deletion.
- Introduce soft delete, undo, background cleanup jobs, or document archival.
- Change upload, retrieval, or chat behavior outside the deletion workflow.

## Decisions

### Treat empty successful responses as valid in the frontend API helper
The shared request helper will recognize response codes that legitimately contain no body, especially `204 No Content`, and return a non-error success value without attempting JSON parsing.

Rationale: the current bug is caused by a contract mismatch, not by a failing delete endpoint. Fixing the helper keeps the frontend aligned with normal HTTP deletion semantics and avoids route-specific parsing workarounds.

Alternatives considered:
- Return JSON from the delete endpoint instead of `204`: possible, but it changes a correct API contract to compensate for a client bug.
- Special-case document deletion in `documentService.delete`: smaller in scope, but leaves the shared request helper incorrect for any other empty success response.

### Keep deletion orchestration in the backend route while using a single transaction boundary
The delete route will continue to coordinate chunk and document removal, but repository behavior will be adjusted so the route can perform both actions within one transaction or one commit path rather than two independent commits.

Rationale: the route is already the owning orchestration point for deletion, and this change only needs transactional cohesion, not a new service layer.

Alternatives considered:
- Add a dedicated deletion service: valid if more delete-related policies emerge, but unnecessary for the current scope.
- Rely only on database cascade behavior: attractive, but would require model or migration changes that are not clearly necessary for this bug fix.

### Preserve current user-facing interaction model with clearer success and failure behavior
The document list component will keep the existing confirmation prompt and refresh pattern, but its success path will depend on the corrected API helper and its failure path will remain tied to explicit backend errors.

Rationale: the UI behavior is already simple and sufficient. The bug is that success is being misclassified as failure.

Alternatives considered:
- Redesign deletion UX with inline notifications: useful later, but not required to restore the broken workflow.

## Risks / Trade-offs

- [Shared API helper change affects other calls] → Mitigation: keep the new behavior narrow to successful empty responses and preserve existing JSON parsing for responses that contain bodies.
- [Transaction handling could require repository signature changes] → Mitigation: confine repository adjustments to commit behavior needed by deletion and validate affected tests around CRUD behavior.
- [Deleting chunks before documents may still fail if route-level orchestration is incomplete] → Mitigation: make the route own the full delete sequence and only finalize once both deletions succeed.
- [Existing tests may not cover real HTTP 204 semantics] → Mitigation: add behavior-focused API tests and one frontend-facing contract test for empty delete responses.

## Migration Plan

No data migration is required.

Deployment steps:
1. Update frontend response handling for successful empty responses.
2. Update backend deletion transaction behavior.
3. Run focused deletion tests and a behavior validation through the actual delete endpoint.

Rollback strategy:
- Revert the frontend helper and backend deletion transaction changes together if deletion regressions appear.

## Open Questions

- Whether the existing database schema already has foreign-key cascade behavior that can simplify the backend delete path should be confirmed during implementation.
- Whether the frontend should eventually surface non-blocking toast feedback instead of browser alerts is left out of scope for this change.