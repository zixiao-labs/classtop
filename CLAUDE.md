# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClassTop is a desktop class schedule manager and display tool built with Tauri 2 + Vue 3 + PyTauri. It features:
- **TopBar**: An always-on-top progress bar showing current class schedule and progress
- **Management UI**: Full-featured schedule management interface
- **Dual Architecture**: Rust (Tauri) + Python (backend logic) + Vue 3 (frontend)

## Development Commands

### Environment Setup

**IMPORTANT: Clone Required Subprojects**

Before setting up the development environment, clone these two subprojects into your workspace:

```bash
# Clone Management Server (enterprise sync backend)
git clone https://github.com/Zixiao-System/Classtop-Management-Server.git

# Clone SDK (Python SDK for ClassTop)
git clone https://github.com/Zixiao-System/classtop-sdk.git
```

These subprojects should be cloned as sibling directories to the main ClassTop repository:
```
workspace/
├── classtop/                      # Main repository (this one)
├── Classtop-Management-Server/    # Management server subproject
└── Classtop-SDK/                  # Python SDK subproject
```

**Install Dependencies:**

```bash
# Install Node.js dependencies
npm install

# Create Python virtual environment
uv venv --python-preference only-system

# Activate virtual environment (Windows PowerShell)
& .venv/Scripts/Activate.ps1

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install Python dependencies
uv pip install -e src-tauri
```

### Development

```bash
# Run development mode (opens TopBar and Main window)
npm run tauri dev

# This starts Vite dev server on port 1420 and launches Tauri
```

### Building

```bash
# Build production bundle (Windows)
./Build.ps1

# Build production bundle (macOS/Linux)
./build.sh

# IMPORTANT: Before building, download CPython to src-tauri/pyembed
# See: https://pytauri.github.io/pytauri/latest/usage/tutorial/build-standalone/
```

### Testing

```bash
# Run Python tests
cd src-tauri
pytest

# Run tests with coverage
pytest --cov=tauri_app --cov-report=html

# Run specific test
pytest tests/test_schedule_manager.py -v

# Run unit tests only
pytest -m unit

# Run integration tests
pytest -m integration
```

## Architecture

### Dual-Window Architecture

ClassTop runs two Tauri windows simultaneously:

1. **TopBar Window** (`/#/topbar`)
   - Always-on-top, transparent, frameless window
   - Displays current class progress and countdown
   - Cannot be closed directly (use tray menu)
   - Located at: `src/TopBar/TopBar.vue`

2. **Main Window** (`/`)
   - Full management interface with navigation
   - Three pages: Home, Schedule Management, Settings
   - Can be minimized to system tray
   - Entry point: `src/Main.vue`

### Frontend-Backend Communication

**Frontend → Python Backend:**
```javascript
import { pyInvoke } from 'tauri-plugin-pytauri-api';

// Call Python command
const result = await pyInvoke('command_name', { param: value });
```

**Python Commands Definition:**
- Located in: `src-tauri/python/tauri_app/commands.py`
- Use `@commands.command()` decorator
- Request/response use Pydantic models
- Commands are registered automatically via PyTauri

**Real-time Updates (Python → Frontend):**
```python
# In Python
from .events import emit_schedule_updated
emit_schedule_updated()

# In Vue
import { listen } from '@tauri-apps/api/event';
listen('schedule-updated', (event) => { /* handle */ });
```

### Data Flow Architecture

```
Vue Components (src/pages/*)
    ↓ pyInvoke
Python Commands (src-tauri/python/tauri_app/commands.py)
    ↓ calls
Manager Classes (schedule_manager.py, settings_manager.py, etc.)
    ↓ operates on
SQLite Database (~/.classtop/classtop.db)
    ↓ emits
Event System (events.py)
    ↑ listens
Vue Components (update UI)
```

### Python Backend Modules

Located in `src-tauri/python/tauri_app/`:

- **commands.py**: Command handlers (API between frontend and Python)
- **db.py**: Database initialization and connection management
- **schedule_manager.py**: Course schedule CRUD operations
- **settings_manager.py**: Application settings management with defaults
- **events.py**: Event system for real-time UI updates
- **sync_client.py**: Management Server synchronization
- **camera_manager.py**: Camera recording functionality
- **audio_manager/**: Real-time audio monitoring with Channel API
- **tray.py**: System tray integration
- **logger.py**: Logging infrastructure

### Frontend Structure

Located in `src/`:

- **Main.vue**: Main window with router and navigation
- **TopBar/TopBar.vue**: Always-on-top schedule display
  - **components/Clock.vue**: Current time display
  - **components/Schedule.vue**: Class progress and countdown
- **pages/**: Application pages
  - **Home.vue**: Welcome screen
  - **SchedulePage.vue**: Course management interface
  - **Settings.vue**: Settings and configuration
  - **AudioMonitor.vue**: Audio monitoring interface
- **utils/**: Shared utilities
  - **schedule.js**: Schedule-related API calls and utilities
  - **config.js**: Settings API wrappers
  - **globalVars.js**: Reactive global state (settings, current week)
  - **collapse.js**: TopBar collapse/expand control
  - **theme.js**: Theme management
  - **notifications.js**: Desktop notifications

## Key Technical Details

### Week Number Calculation

ClassTop uses ISO weekday format (1=Monday, 7=Sunday) throughout the codebase.

**Two modes:**
1. **Automatic**: Set `semester_start_date` (YYYY-MM-DD), week calculated from current date
2. **Manual** (deprecated): Directly set week number in database

```python
# In schedule_manager.py
def calculate_week_number(semester_start_date: str) -> int:
    # Calculates weeks elapsed since semester start
    # Used by get_calculated_week_number()
```

### Schedule Display Algorithm

Located in `src/TopBar/components/Schedule.vue`:

**Logic:**
1. Fetch all classes for current day
2. Check if any class is in progress (current time within start-end)
3. If in progress: show progress bar
4. If between classes: show countdown to next class with actual interval duration
5. If all classes ended today: show tomorrow's first class

**Important:** Uses actual time difference between classes, not fixed interval assumptions.

### Database Schema

SQLite database at `~/.classtop/classtop.db`:

```sql
-- courses: Basic course information
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    teacher TEXT,
    location TEXT,
    color TEXT
);

-- schedule: Course schedule entries
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    day_of_week INTEGER,  -- 1=Monday, 7=Sunday (ISO format)
    start_time TEXT,      -- HH:MM format
    end_time TEXT,
    weeks TEXT,           -- JSON array: [1,2,3,...]
    note TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- config: Key-value settings storage
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

### Settings Management

All settings have defaults defined in `settings_manager.py::DEFAULT_SETTINGS`.

**Key settings:**
- `semester_start_date`: For automatic week calculation
- `theme_mode`: 'auto' | 'dark' | 'light'
- `theme_color`: Material Design color (hex)
- `sync_enabled`: Enable Management Server sync
- `server_url`: Management Server endpoint
- `client_uuid`: Unique client identifier
- `reminder_enabled`: Enable course reminders
- `reminder_minutes`: Minutes before class to remind

### Management Server Integration

**Two server options:**

1. **admin-server** (local WebSocket control):
   - Located in `admin-server/` directory
   - FastAPI + WebSocket for real-time control
   - Run: `cd admin-server && python main.py`

2. **Management-Server** (enterprise sync):
   - External repo: Zixiao-System/Classtop-Management-Server
   - RESTful API for multi-client data sync
   - Client implementation: `sync_client.py`
   - Commands: `test_server_connection()`, `sync_now()`, `register_to_server()`

### Audio Monitoring Architecture

Uses PyTauri's Channel API for real-time streaming:

```python
# Backend (commands.py)
@commands.command()
async def start_audio_monitoring(
    body: StartAudioMonitoringRequest,
    webview_window: WebviewWindow
) -> AudioMonitoringResponse:
    channel = body.channel_id.channel_on(webview_window.as_ref_webview())

    def callback(level):
        data = AudioLevelData(timestamp=..., rms=..., db=..., peak=...)
        channel.send_model(data)

    audio_manager.start_monitoring(callback=callback)
```

```javascript
// Frontend (AudioMonitor.vue)
import { Channel } from 'tauri-plugin-pytauri-api';

const channel = new Channel();
await pyInvoke('start_audio_monitoring', {
  monitor_type: 'microphone',
  channel_id: channel.id
});

channel.onmessage = (data) => {
  // Handle real-time audio level data
};
```

### Conflict Detection

When adding/editing schedule entries, `check_schedule_conflict` validates:
- Time overlap on same day
- Week number conflicts (checks weeks array intersection)
- Returns conflicting entries with specific conflict weeks

## Testing Strategy

### Python Tests

Located in `src-tauri/tests/`:

- **test_schedule_manager.py**: Schedule CRUD and conflict detection
- **test_settings_manager.py**: Settings initialization and updates
- **test_db.py**: Database operations
- **test_commands.py**: Command handlers
- **test_events.py**: Event emission
- **test_sync_client.py**: Server synchronization

**Test database:** Uses temporary in-memory SQLite database for isolation

**Pytest markers:**
- `@pytest.mark.unit`: Unit tests (fast)
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.windows_only`: Windows-specific tests

### Running Tests

```bash
cd src-tauri

# All tests
pytest

# Specific marker
pytest -m unit

# With coverage
pytest --cov=tauri_app --cov-report=html

# Verbose output
pytest -v -s
```

## Common Development Scenarios

### Adding a New Python Command

1. Define request/response models in `commands.py`:
```python
class MyRequest(BaseModel):
    param1: str
    param2: int

class MyResponse(BaseModel):
    result: str
```

2. Implement command handler:
```python
@commands.command()
async def my_command(body: MyRequest) -> MyResponse:
    # Implementation
    return MyResponse(result="...")
```

3. Add permission in `src-tauri/capabilities/default.json`:
```json
{
  "permissions": [
    "pytauri:allow-my_command"
  ]
}
```

4. Call from frontend:
```javascript
const result = await pyInvoke('my_command', { param1: 'value', param2: 42 });
```

### Adding a New Setting

1. Add default to `settings_manager.py::DEFAULT_SETTINGS`:
```python
DEFAULT_SETTINGS = {
    'my_setting': 'default_value',
    # ...
}
```

2. Add to global state in `src/utils/globalVars.js`:
```javascript
export const settings = reactive({
    my_setting: 'default_value',
    // ...
});
```

3. Access in components:
```javascript
import { settings, loadSettings } from '@/utils/globalVars.js';

// Read
console.log(settings.my_setting);

// Update (saves to database automatically)
settings.my_setting = 'new_value';
```

### Adding Real-time Events

1. Define event in `events.py`:
```python
def emit_my_event(data: dict):
    if event_handler:
        event_handler.emit("my-event", data)
```

2. Listen in Vue component:
```javascript
import { listen } from '@tauri-apps/api/event';

listen('my-event', (event) => {
    console.log('Event data:', event.payload);
});
```

## Platform-Specific Notes

### Windows
- Virtual environment activation: `.venv\Scripts\Activate.ps1`
- Build script: `Build.ps1`
- Audio monitoring uses `pycaw` for system audio loopback

### macOS
- Virtual environment: `source .venv/bin/activate`
- Build script: `build.sh`
- Requires Xcode command line tools

### Linux
- `glib` dependency required (only on Linux, specified in Cargo.toml)
- May need additional system packages for camera/audio support

## Important Files and Their Purposes

- **tauri.conf.json**: Window configuration, permissions, build settings
- **Cargo.toml**: Rust dependencies, PyTauri configuration
- **pyproject.toml**: Python dependencies, pytest configuration
- **capabilities/default.json**: Frontend permission whitelist
- **vite.config.js**: Vite dev server, MDUI custom element configuration

## Course Reminder System

Located in `src-tauri/python/tauri_app/reminder_manager.py`:

- Background thread checks upcoming classes
- Sends desktop notifications before class starts
- Configurable reminder time (5/10/15/30 minutes before)
- Optional sound notification
- Automatically runs when app starts if enabled

## Troubleshooting

### PyTauri Command Not Found
- Check `capabilities/default.json` for permission
- Ensure `@commands.command()` decorator is present
- Verify command is imported in `__init__.py`

### Database Locked Error
- Close all app instances
- Check for orphaned processes
- Database uses proper context managers for connection handling

### TopBar Not Updating
- Check `Schedule.vue` refresh intervals (1s for display, 10s for data)
- Verify event listeners are properly registered
- Check browser console for pyInvoke errors

### Build Fails
- Ensure CPython is downloaded to `src-tauri/pyembed`
- Check Python dependencies are installed: `uv pip install -e src-tauri`
- Verify Node dependencies: `npm install`
