## ADDED Requirements

### Requirement: Persistent Watch History
The system SHALL track and persist watch history in local database.

#### Scenario: Record watched movie
- **WHEN** movie playback completes (>30 seconds watched)
- **THEN** system records in history: title, media_type=movie, watch_date, duration_watched
- **AND** stores in SQLite database: ~/.local/share/comando-cli/history.db

#### Scenario: Record watched series episode
- **WHEN** series episode playback completes (>30 seconds watched)
- **THEN** system records: title, media_type=series, season, episode_num, watch_date
- **AND** updates "last_watched_episode" for that series
- **AND** stores in database

#### Scenario: Partial playback not recorded
- **WHEN** user stops playback after <30 seconds
- **THEN** system does not add entry to watch history
- **AND** shows message: "Playback too short (<30s); not recording"

### Requirement: Resume Functionality
The system SHALL allow users to resume watching from last episode.

#### Scenario: Resume series playback
- **WHEN** user runs `comando resume` or `comando watch --resume`
- **THEN** system queries database for most recent series watched
- **AND** displays: "Resume 'Demolidor' from episode 5?"
- **AND** pressing Y auto-selects: title + season + episode 5

#### Scenario: No resume available
- **WHEN** user runs `comando resume` with no watch history
- **THEN** system shows: "No resume available"
- **AND** prompts for new search

#### Scenario: Resume with episode range
- **WHEN** user resumes series from episode 5
- **AND** was previously watching episodes 5-8
- **THEN** system resumes from episode 5 with same quality/language as before
- **AND** continues through remaining episodes in range

### Requirement: Watch History Query
The system SHALL provide commands to view and query watch history.

#### Scenario: List recent watches
- **WHEN** user runs `comando history` or `comando history --recent`
- **THEN** system displays last 10 watched titles with dates:
  ```
  1. Demolidor S1E5 - 2024-02-23 19:35
  2. Avatar - 2024-02-22 21:10
  3. Breaking Bad S2E3 - 2024-02-20 18:45
  ```

#### Scenario: Filter by media type
- **WHEN** user runs `comando history --type series`
- **THEN** system shows only series watches

#### Scenario: Search history
- **WHEN** user runs `comando history --search demolidor`
- **THEN** system shows all history entries matching "demolidor"

### Requirement: History Storage Location
The system SHALL store watch history using XDG Base Directory specification.

#### Scenario: Create history database
- **WHEN** user watches first item
- **THEN** system creates directory: ~/.local/share/comando-cli/
- **AND** creates SQLite database: history.db
- **AND** initializes schema with tables: watch_history, titles

#### Scenario: History persists across sessions
- **WHEN** user watches item in session 1
- **AND** then runs `comando resume` in session 2 (next day)
- **THEN** resume works correctly from last watched episode

### Requirement: Watch History Cleanup
The system SHALL provide options to manage history database.

#### Scenario: Clear all history
- **WHEN** user runs `comando history --clear-all`
- **THEN** system prompts: "Delete all watch history? This cannot be undone. (y/n)"
- **AND** deletes database if user confirms

#### Scenario: Clear old entries
- **WHEN** user runs `comando history --cleanup-days 30`
- **THEN** system deletes entries older than 30 days
- **AND** shows: "Deleted X entries older than 30 days"

### Requirement: Remember Quality/Language Preferences
The system SHALL store user's quality/language choices per title.

#### Scenario: Reuse previous selection
- **WHEN** user watches series with quality=1080p + language=Portuguese (Dub)
- **AND** watches same series again
- **THEN** system proposes: "Use previous quality/language? (1080p, Portuguese) [y/n]"
- **AND** auto-selects if user confirms

#### Scenario: Override stored preference
- **WHEN** user selects different quality/language than stored
- **THEN** system updates preference for next watch
- **AND** shows: "Updated preference for this title"
