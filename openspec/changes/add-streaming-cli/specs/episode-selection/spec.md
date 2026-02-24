## ADDED Requirements

### Requirement: Flexible Episode Range Selection
The system SHALL support multiple episode selection syntaxes via `-e` flag for series.

#### Scenario: Single episode
- **WHEN** user runs `comando search demolidor -e 5`
- **THEN** system selects only episode 5
- **AND** proceeds to quality/language selection for that episode

#### Scenario: Episode range
- **WHEN** user runs `comando search demolidor -e 2-5`
- **THEN** system selects episodes 2, 3, 4, 5
- **AND** user is prompted to play each in sequence

#### Scenario: Open-ended range (from episode to end)
- **WHEN** user runs `comando search demolidor -e 5-`
- **THEN** system selects episodes 5 through total episode count
- **AND** plays each in sequence

#### Scenario: Open-ended range (first N episodes)
- **WHEN** user runs `comando search demolidor -e -3`
- **THEN** system selects episodes 1, 2, 3
- **AND** plays each in sequence

#### Scenario: Invalid episode range
- **WHEN** user enters episode range exceeding total episodes (e.g., `-e 50-60` for 13-episode series)
- **THEN** system shows error: "Series has only 13 episodes. Valid range: 1-13"
- **AND** prompts for corrected input or exits

#### Scenario: Invalid range syntax
- **WHEN** user enters malformed range (e.g., `-e 2--5` or `-e abc`)
- **THEN** system shows error: "Invalid episode format. Use: -e 5, -e 2-5, -e 2-, or -e -5"
- **AND** exits with status code 1

### Requirement: Ignored for Movies
The system SHALL ignore `-e` flag when media_type is movie.

#### Scenario: Movie ignores -e flag
- **WHEN** user runs `comando search avatar -e 2`
- **AND** "Avatar" is identified as movie
- **THEN** system ignores the `-e 2` flag
- **AND** proceeds directly to quality/language selection for the movie
- **AND** shows info message: "Avatar is a movie; -e flag ignored"

### Requirement: Sequential Episode Playback
The system SHALL handle multiple episode playback with user prompts between episodes.

#### Scenario: Play next episode
- **WHEN** playback of episode N completes
- **AND** N+1 is in selected range
- **THEN** system prompts: "Play next episode (Y/n)?"
- **AND** waits for user input or auto-continues after timeout (10s)

#### Scenario: Interrupt series playback
- **WHEN** user selects "n" or interrupts (Ctrl+C) during multi-episode session
- **THEN** system stops playback
- **AND** updates watch history with last completed episode
- **AND** exits cleanly
