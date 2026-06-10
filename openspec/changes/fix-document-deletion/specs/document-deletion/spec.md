## ADDED Requirements

### Requirement: User can delete an uploaded document from the document list
The system SHALL allow a user to delete an uploaded document from the document list and SHALL treat a successful deletion response as success even when the API returns no response body.

#### Scenario: Successful deletion with empty response body
- **WHEN** the user confirms deletion of an existing document and the API responds with a successful `204 No Content`
- **THEN** the system removes the document from the list without showing an error

#### Scenario: Deleting the selected document clears the active filter
- **WHEN** the user deletes the document currently selected for chat filtering
- **THEN** the system clears the selected document filter

### Requirement: Document deletion removes associated chunks as one logical operation
The system SHALL remove a document and its associated chunks together so that a failed delete operation does not leave only part of the document data removed.

#### Scenario: Successful deletion removes all related data
- **WHEN** the system deletes an existing document
- **THEN** the document record and all chunks linked to that document are removed

#### Scenario: Deletion failure preserves consistency
- **WHEN** an error occurs before the delete operation is fully completed
- **THEN** the system preserves a consistent state and reports the deletion as failed

### Requirement: Deletion failures are reported accurately
The system SHALL show deletion errors to the user only when the backend deletion request fails or the target document does not exist.

#### Scenario: Document does not exist
- **WHEN** the user attempts to delete a document that is no longer present
- **THEN** the system reports that the deletion failed

#### Scenario: Backend deletion error
- **WHEN** the deletion request returns a non-success status
- **THEN** the system shows an error state instead of removing the document locally