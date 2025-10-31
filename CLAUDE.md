# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClassTop is a desktop course management and display tool built with Tauri 2 + Vue 3 + PyTauri. It provides an always-on-top progress bar showing current/next classes and a full-featured management interface.

**Key Features:**
- Real-time course progress display with always-on-top transparent window
- Full course schedule CRUD operations
- SQLite-based data persistence
- System tray integration
- Automatic/manual week number calculation
- WebSocket-based remote control via LMS (Light Management Service)
- Camera monitoring support (Windows only)

## Tech Stack

**Frontend:**
- Vue 3 (Composition API) + Vue Router 4
- Vite 6 as build tool
- MDUI 2.1.4 (Material Design components)
- Less for styling

**Backend:**
- Tauri 2 framework (Rust)
- PyTauri 0.8 for Python-Rust integration
- Python 3.10+ backend logic
- SQLite database

## Application Icons

The application uses icons located in the following directories:

**Source Icon:**
- `icons/Icon-iOS-Default-1024x1024@1x.png` - 1024x1024 source image

**Application Icons** (located in `src-tauri/icons/`):
- PNG icons: 32x32.png, 128x128.png, 128x128@2x.png (256x256), icon.png (512x512)
- macOS icon: icon.icns (multi-resolution bundle)
- Windows icon: icon.ico (multi-resolution bundle)
- Windows Store icons: Square30x30Logo.png through Square310x310Logo.png, StoreLogo.png

**Icon Configuration:**
Icons are configured in `src-tauri/tauri.bundle.json` under the `bundle.icon` array. All icons are automatically generated from the source PNG using platform-specific tools (sips for PNG/ICNS on macOS, ImageMagick for ICO files).

## Development Commands

### Development Mode
```bash
npm run tauri dev
```
This starts both windows:
- **main** window (1200x800): Course management interface at `/#/`
- **topbar** window (1400x50): Always-on-top progress bar at `/#/topbar`

**Note**: Frontend hot reloads automatically, but Python changes require restarting `npm run tauri dev`

### Build for Production

**Prerequisites**: Download CPython to `src-tauri/pyembed` following [PyTauri Build Standalone Binary](https://pytauri.github.io/pytauri/latest/usage/tutorial/build-standalone/)

**Windows**:
```powershell
./Build.ps1
```

**Manual build**:
```bash
# Set Python path
export PYO3_PYTHON="./src-tauri/pyembed/python/python.exe"  # Windows
# or
export PYO3_PYTHON="./src-tauri/pyembed/python/bin/python3"  # Linux/macOS

# Install Python package
uv pip install --exact --python="$PYO3_PYTHON" --reinstall-package=classtop ./src-tauri

# Build Tauri app
npm run -- tauri build --config="src-tauri/tauri.bundle.json" -- --profile bundle-release
```

Build artifacts located at `src-tauri/target/bundle-release/`

### Code Quality Checks

```bash
# Rust formatting check
cargo fmt --manifest-path=src-tauri/Cargo.toml --all -- --check

# Rust linting (strict mode)
cargo clippy --manifest-path=src-tauri/Cargo.toml --all-targets --all-features -- -D warnings

# Rust build verification
cargo build --manifest-path=src-tauri/Cargo.toml --release --features pytauri/standalone
```

### Frontend Only Development
```bash
npm run dev        # Start Vite dev server on port 1420
npm run build      # Build frontend to dist/
```

### Dependencies
```bash
npm install        # Install Node.js dependencies (no package-lock.json by design)
```

## Architecture

### Dual-Window System
The application uses Tauri's multi-window feature with distinct purposes:

1. **TopBar Window** (`/#/topbar`):
   - Always-on-top, transparent, borderless window
   - Displays Clock.vue (left) + Schedule.vue (right)
   - Updates every second for progress, every 10s for data refresh
   - Configuration: `src-tauri/tauri.conf.json` lines 14-41
   - Has `closable: false` to prevent accidental closure

2. **Main Window** (`/#/`):
   - Standard window with navigation
   - Routes: Home, SchedulePage, Settings
   - Uses Main.vue wrapper component
   - Starts hidden (`visible: false`), shown by system tray

### Python-Rust Communication Flow

```
Vue Frontend
  ↓ pyInvoke('command_name', params)
Python Commands (commands.py)
  ↓ uses
Database Layer (db.py) + Managers (schedule_manager.py, settings_manager.py)
  ↓ emits events via
Event Handler (events.py)
  ↓ Emitter.emit()
Vue Frontend receives events
```

**Key Pattern:** All Python commands are registered via `@commands.command()` decorator in `commands.py`. Frontend calls them using `pyInvoke()` from `tauri-plugin-pytauri-api`. `pyInvoke()` is async - always await the call.

### Database Schema

SQLite database at runtime: `classtop.db` (location in Tauri's app data directory; check logs for exact path)

**Tables:**
- `courses`: Course information (id, name, teacher, location, color)
- `schedule`: Schedule entries (id, course_id, day_of_week, start_time, end_time, weeks as JSON)
  - `day_of_week`: ISO format (1=Monday, 7=Sunday)
  - `weeks`: JSON array like `[1,2,3,...]` indicating which weeks this entry applies
- `config`: Key-value configuration store

### Event System

The application uses a singleton `EventHandler` (`events.py`) for real-time updates:

- **Thread-safe:** Uses async portal for cross-thread event emission
- **Events emitted:**
  - `schedule-update`: When courses/schedules change (types: course_added, course_updated, course_deleted, schedule_added, schedule_deleted)
  - `setting-update`: When single setting changes
  - `settings-batch-update`: When multiple settings update

Frontend components listen via Tauri event listeners to auto-refresh data.

### Week Number Calculation

Two modes (managed by `settings_manager.py`):

1. **Automatic (preferred):** Set `semester_start_date` in config, calculates current week from today's date
2. **Manual (deprecated):** Directly set `current_week` config value

Week calculation logic in `db.py:get_calculated_week_number()` - prioritizes semester_start_date if present.

**Calculation**: `floor((today - start_date).days / 7) + 1`

**Edge cases**: When semester_start_date is cleared, falls back to manual week (default 1)

### Schedule Display Logic

Located in `src/TopBar/components/Schedule.vue` and `src/utils/schedule.js`:

**States:**
1. **During class:** Shows course name, location, time range, progress bar (0-100%)
2. **Break time:** Shows "Next: [course]" with countdown timer
3. **Day ended:** Shows tomorrow's first class

**Important:** Uses `getScheduleForWeek()` to fetch entire week, then client-side calculates current/next class. This avoids deprecated server-side `get_current_class()` endpoints.

**Cross-day logic:** `findNextClassAcrossWeek()` in `schedule.js` handles next-day lookup when today's classes are over.

### Python Module Structure

`src-tauri/python/tauri_app/`:

- `__init__.py`: Application entry point, initializes all managers and event system
- `commands.py`: Pydantic-based command definitions for frontend-backend interface
- `db.py`: Raw SQLite operations, connection management
- `schedule_manager.py`: Business logic for schedule CRUD (uses db.py, emits events)
- `settings_manager.py`: Manages application settings with defaults
- `api_server.py`: Optional HTTP API server for remote management (FastAPI-based)
- `events.py`: Thread-safe singleton event handler
- `tray.py`: System tray menu (show/hide windows, quit)
- `logger.py`: Logging utilities with file rotation (accessible via `get_logs` command, max 200 lines default)
- `websocket_client.py`: WebSocket client for connecting to LMS
- `camera_manager.py`: Camera monitoring manager (Windows only)

**Initialization order** (in `__init__.py:main()`):
1. Logger
2. Async portal (for thread-safe async operations)
3. Event handler
4. Database
5. Settings manager (initializes defaults)
6. Schedule manager
7. WebSocket client (if configured)
8. Camera manager (if enabled and Windows platform)
9. API server (if enabled in settings)
10. System tray

**Platform-specific initialization**:
- Camera manager only initializes on Windows (`platform.system() == "Windows"`)
- Import of `camera_manager` is delayed until runtime to avoid import errors on non-Windows platforms

### Frontend Module Structure

`src/`:

- `main.js`: App entry, router setup, MDUI import
- `App.vue`: Root component
- `Main.vue`: Layout wrapper for main window (navigation + router-view)
- `TopBar/TopBar.vue`: TopBar window root
- `TopBar/components/Clock.vue`: Time display
- `TopBar/components/Schedule.vue`: Course progress/countdown logic
- `pages/Home.vue`: Welcome page
- `pages/SchedulePage.vue`: Full course schedule management
- `pages/Settings.vue`: Week/semester settings
- `utils/schedule.js`: Shared utilities for time calculations, API calls (pyInvoke wrappers)
- `utils/globalVars.js`: Global reactive variable management
- `utils/collapse.js`: TopBar collapse control
- `utils/config.js`: Settings operation interface
- `router/index.js`: Route definitions

**Important**: MDUI components use custom elements (`tag.startsWith('mdui-')`), configured in `vite.config.js`

### LMS (Light Management Service)

ClassTop includes a companion LMS for local network management. Located in `lms/` directory.

**Features:**
- WebSocket-based real-time control of multiple clients
- Remote settings management
- Camera monitoring control
- SQLite-based client registry and command logging
- Optional Management-Server integration (enterprise-grade central hub)

**LMS Server Structure** (`lms/`):
```
lms/
├── main.py                    # FastAPI application entry
├── websocket_manager.py       # WebSocket connection manager
├── models.py                  # Data models
├── db.py                      # SQLite database layer
├── management_client.py       # Management-Server integration client
├── api/                       # API endpoints
│   ├── clients.py            # Client management
│   ├── settings.py           # Settings management
│   └── cctv.py               # Camera control
└── static/                    # Web management UI
    ├── index.html
    ├── style.css
    └── app.js
```

**Starting LMS**:
```bash
cd lms
pip install -r requirements.txt
python main.py
```

Access management interface at `http://localhost:8000`

**Client Configuration**:
- `server_url`: WebSocket URL of LMS (e.g., `ws://localhost:8000`)
- `client_uuid`: Auto-generated client identifier

**Communication Flow**:
1. Client connects via WebSocket on startup (if `server_url` configured)
2. Client registers with UUID and metadata
3. LMS sends commands via WebSocket
4. Client responds with execution results
5. Heartbeat every 30 seconds to maintain connection

### API Server (Optional)

ClassTop includes an optional HTTP API server for centralized management.

**Location:** `src-tauri/python/tauri_app/api_server.py`

**Features:**
- RESTful HTTP endpoints for all CRUD operations
- FastAPI-based implementation with automatic OpenAPI documentation
- Runs in background daemon thread (non-blocking)
- Configurable via settings (enabled/disabled, host, port)

**Configuration Settings:**
- `api_server_enabled`: "true"/"false" - Enable/disable API server
- `api_server_host`: Default "0.0.0.0" - Listening address
- `api_server_port`: Default "8765" - Listening port

**Access Points:**
- API Base: `http://localhost:8765/api/`
- Swagger UI: `http://localhost:8765/api/docs`
- ReDoc: `http://localhost:8765/api/redoc`

**Initialization:**
API server is conditionally initialized in `__init__.py:main()` after schedule/settings managers, only if `api_server_enabled` is "true".

**Dependencies:**
Requires `fastapi` and `uvicorn` packages. If not installed, API server silently disables with warning in logs.

**Documentation:**
- Full API reference: `docs/API.md`
- Quick start guide: `docs/API_QUICKSTART.md`

## Important Patterns

### Adding a New Python Command

1. Define request/response models in `commands.py` using Pydantic
2. Add `@commands.command()` decorated async function
3. Implement logic (usually delegates to db.py or managers)
4. Export wrapper in `src/utils/schedule.js` using `pyInvoke()`
5. Add to capabilities if needed: `src-tauri/capabilities/default.json`

### Time Format Consistency

- **Storage:** HH:MM string format (e.g., "14:30")
- **Day of week:** ISO 8601 (1-7, Monday=1, Sunday=7)
- **Parsing:** Use `parseTime()` from `schedule.js` to get `{hour, minute}` objects
- **Progress calculation:** Include seconds for smooth progress bars (`calculateCourseProgress()`)

### Cross-day Schedule Queries

When today's classes end, frontend must query next day:
- Use `getScheduleForWeek()` to get all week data once
- Use `findNextClassAcrossWeek()` to find cross-day next class
- Avoids multiple Python calls and handles week wraparound

### Platform-Specific Code

**Camera Manager (Windows Only)**:
```python
import platform

if platform.system() == "Windows":
    from .camera_manager import CameraManager
    # Initialize camera manager
else:
    logger.log_message("info", "Camera manager not initialized: platform is not Windows")
```

**Pattern**: Import platform-specific modules conditionally at runtime, not at module level, to prevent import errors.

## Common Issues

### PyTauri Integration
- All Python dependencies must be available at runtime (PyTauri bundles Python environment)
- `pyInvoke()` is async - always await the call
- Event emission from non-async-loop threads uses the portal (handled automatically by EventHandler)

### Window Management
- TopBar window has `closable: false` to prevent accidental closure
- Both windows defined in `tauri.conf.json` app.windows array
- Main window starts hidden (`visible: false`), shown by system tray

### Week Calculation Edge Cases
- When semester_start_date is cleared, falls back to manual week (default 1)
- Week numbers calculated as floor((today - start_date).days / 7) + 1
- Frontend must call `get_current_week()` to get computed week info

### CI/CD
- **No package-lock.json**: Project intentionally excludes package-lock.json from VCS
- Use `npm install` (not `npm ci`) in scripts
- GitHub Actions: No npm cache configuration (requires lock file)

### Platform Compatibility
- Camera features only work on Windows
- Always check `platform.system()` before initializing platform-specific features
- Use delayed imports for platform-specific modules

## Related Projects

### Management-Server (Enterprise)
- **Repository**: [Classtop-Management-Server](https://github.com/Zixiao-System/Classtop-Management-Server)
- **Tech Stack**: Rust + Actix-Web + PostgreSQL + Vue 3
- **Purpose**: Enterprise-grade centralized management server
- **Features**: Multi-client data sync, analytics, WebSocket control, LMS instance management

**Integration Docs**:
- `docs/DUAL_TRACK_ARCHITECTURE.md`: Comprehensive dual-track architecture guide
- `docs/MANAGEMENT_SERVER_IMPROVEMENT_PLAN.md`: Improvement plans
- `docs/QUICK_START_SYNC.md`: 5-step sync guide
- `docs/CLIENT_ADAPTATION.md`: Client integration details

### LMS vs Management-Server
- **LMS**: Lightweight, local network, WebSocket-based, 10-50 clients
- **Management-Server**: Enterprise, centralized, PostgreSQL, hundreds-thousands of clients
- **Dual-track**: Clients can connect to both simultaneously (LMS for real-time control, Management-Server for data analytics)

## Development Documentation

### Platform Setup Guides
- `docs/LINUX_SETUP.md`: Ubuntu/Debian/Fedora/Arch Linux setup
- `docs/MACOS_SETUP.md`: macOS setup (Intel/Apple Silicon)
- README.md: Windows setup (PowerShell commands)

### IDE Configuration Guides
- `docs/VSCODE_SETUP.md`: VSCode configuration (all platforms)
- `docs/XCODE_SETUP.md`: Xcode configuration (macOS debugging/profiling)
- `docs/VISUAL_STUDIO_SETUP.md`: Visual Studio configuration (Windows debugging/profiling)

### API Documentation
- `docs/API.md`: Complete HTTP API reference
- `docs/API_QUICKSTART.md`: API usage examples
- `lms/README.md`: LMS API documentation
