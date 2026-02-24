## ADDED Requirements

### Requirement: Quality Selection Menu
The system SHALL present interactive menu for selecting video quality.

#### Scenario: Display quality options
- **WHEN** metadata is fetched for selected title
- **THEN** system extracts all available quality options (e.g., 720p, 1080p, 4K)
- **AND** displays numbered menu: "1) 720p  2) 1080p  3) 4K"
- **AND** prompts "Select quality:"

#### Scenario: User selects quality
- **WHEN** user enters valid number
- **THEN** system stores selected quality
- **AND** proceeds to language selection menu

#### Scenario: Invalid quality selection
- **WHEN** user enters number outside range
- **THEN** system shows error: "Invalid selection. Enter number 1-N"
- **AND** redisplays menu

### Requirement: Language Selection Menu
The system SHALL present interactive menu for selecting audio/subtitle language.

#### Scenario: Display language options
- **WHEN** quality is selected
- **THEN** system extracts available language/dub options for that quality
- **AND** displays numbered menu: "1) Portuguese (Dub)  2) English (Dub)  3) Portuguese (Subs)"
- **AND** prompts "Select language/dub:"

#### Scenario: User selects language
- **WHEN** user enters valid number
- **THEN** system retrieves magnet link for selected quality + language combination
- **AND** proceeds to torrent streaming

#### Scenario: Only one option available
- **WHEN** quality/language combination has single option
- **THEN** system auto-selects it
- **AND** shows message: "Selected: 720p Portuguese (Dub)" [auto-selected]
- **AND** proceeds to playback

### Requirement: Torrent Streaming with webtorrent
The system SHALL download torrent file to local cache using webtorrent and monitor playability.

#### Scenario: Start torrent download
- **WHEN** magnet link is obtained
- **THEN** system creates cache directory: ~/.cache/comando-cli/torrents/{title-id}/
- **AND** launches webtorrent process with magnet link
- **AND** shows progress: "Downloading torrent... [████░░░░░░] 40%"

#### Scenario: Monitor playable state
- **WHEN** webtorrent begins downloading
- **THEN** system polls downloaded file until first video chunk is available
- **AND** once playable threshold reached (>50MB or time-based heuristic)
- **AND** launches mpv

#### Scenario: Timeout on stalled download
- **WHEN** torrent download stalls for >60 seconds
- **THEN** system shows warning: "Torrent download stalled. Retrying..."
- **AND** attempts download from alternative magnet if available
- **AND** fails with error after 3 retries

#### Scenario: Playback in progress
- **WHEN** mpv is launched and playing
- **THEN** webtorrent continues downloading in background
- **AND** system monitors both processes
- **AND** shows notification when fully downloaded: "Torrent fully downloaded!"

### Requirement: Playback Completion Cleanup
The system SHALL terminate torrent process when playback ends.

#### Scenario: Normal playback completion
- **WHEN** mpv closes (video ends or user closes)
- **THEN** system terminates webtorrent process
- **AND** clears temporary file
- **AND** returns to CLI

#### Scenario: Early termination
- **WHEN** user interrupts playback (Ctrl+C or closes mpv window)
- **THEN** system terminates webtorrent
- **AND** removes partial file
- **AND** updates watch history (if >30 seconds watched)
- **AND** returns to CLI

### Requirement: Error Handling for Playback
The system SHALL handle common playback errors gracefully.

#### Scenario: Invalid torrent/magnet
- **WHEN** torrent fails to load (404, corrupted magnet)
- **THEN** system shows error: "Unable to load torrent. Try different quality."
- **AND** offers option to go back to quality menu or exit

#### Scenario: Insufficient disk space
- **WHEN** ~/.cache/ has <5GB available
- **THEN** system warns: "Low disk space (X GB available). Continue anyway? (y/n)"
- **AND** proceeds if user confirms

#### Scenario: Network interruption
- **WHEN** internet connection drops during playback
- **THEN** mpv may pause
- **AND** webtorrent continues when connection restored
- **AND** system shows info: "Network restored. Resuming..."
