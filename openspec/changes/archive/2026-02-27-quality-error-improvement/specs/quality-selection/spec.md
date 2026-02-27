## ADDED Requirements

### Requirement: Descriptive error for empty episode quality options

When a user selects an episode for a series that has no quality options, the system SHALL display a clear error message indicating the issue, rather than a generic "No quality selected" message.

#### Scenario: Episode has no quality options

- **GIVEN** a title with quality options for episodes 1-3
- **AND** the user specifies episode 5 (which has no quality options)
- **WHEN** quality selection is invoked
- **THEN** the system SHALL display an error message indicating no quality options exist for that episode
- **AND** the message MUST include the episode number for clarity
