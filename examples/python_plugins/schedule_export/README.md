# Schedule Export Plugin

An advanced example demonstrating file operations, external library integration, and multiple export formats.

## Features

- ✅ Export to multiple formats: CSV, JSON, iCal
- ✅ External library integration (icalendar)
- ✅ File system operations
- ✅ User-configurable export options
- ✅ Frontend export interface
- ✅ Event notifications on export completion

## Installation

1. Install optional dependencies:

```bash
pip install icalendar>=5.0.0
```

2. Copy this directory to your ClassTop plugins folder:

```bash
cp -r schedule_export ~/.classtop/plugins/
```

3. Restart ClassTop or reload plugins

4. Enable the plugin in Settings → Plugin Management

## Export Formats

### 1. CSV (Comma-Separated Values)

Exports schedule as a spreadsheet-compatible CSV file.

**Format:**
```csv
Day,Start Time,End Time,Course,Teacher,Location
Monday,08:00,09:40,Mathematics,Prof. Smith,A101
Monday,10:00,11:40,Physics,Dr. Johnson,B202
```

**Use cases:**
- Import into Excel, Google Sheets
- Data analysis with pandas
- Simple backup format

### 2. JSON (JavaScript Object Notation)

Exports schedule as structured JSON data.

**Format:**
```json
{
  "week": 1,
  "export_date": "2025-11-01T10:30:00",
  "schedule": {
    "Monday": [
      {
        "start_time": "08:00",
        "end_time": "09:40",
        "course": {
          "name": "Mathematics",
          "teacher": "Prof. Smith",
          "location": "A101",
          "color": "#FF5733"
        }
      }
    ]
  }
}
```

**Use cases:**
- Web application integration
- API data exchange
- Programmatic processing

### 3. iCal (iCalendar)

Exports schedule as iCalendar format (.ics) for calendar applications.

**Use cases:**
- Import to Google Calendar
- Apple Calendar / Outlook
- Mobile calendar apps

**Requirements:**
- Semester start date must be configured
- `icalendar` Python library installed

## Configuration

Customize export behavior:

- **Default Export Format**: csv, json, or ical
- **Include Teacher**: Add teacher information to exports
- **Include Location**: Add location information to exports
- **Export All Weeks**: Export all weeks or single week (future feature)

## Export Location

Files are saved to: `~/.classtop/exports/`

Filenames follow the pattern:
- `schedule_week_1_20251101_103000.csv`
- `schedule_week_1_20251101_103000.json`
- `schedule_week_1_20251101_103000.ics`

## Usage

### From Frontend

1. Navigate to Settings → Plugin Management → Schedule Export
2. Select export format (CSV, JSON, or iCal)
3. Enter week number (or leave empty for current week)
4. Click "Export Schedule"
5. File is saved to export directory

### Programmatically

```python
# Export current week as CSV
filepath = await plugin.export_to_csv()

# Export specific week as JSON
filepath = await plugin.export_to_json(week=5)

# Export as iCal
filepath = await plugin.export_to_ical()

# Use generic export method
filepath = await plugin.export_schedule(export_format="csv", week=1)
```

## Events

### Emitted Events

#### `schedule_exported`
```json
{
  "format": "csv",
  "filename": "schedule_week_1_20251101_103000.csv",
  "week": 1,
  "path": "/home/user/.classtop/exports/schedule_week_1_20251101_103000.csv"
}
```

## Code Structure

```
schedule_export/
├── plugin.yaml      # Plugin metadata with external dependencies
├── plugin.py        # Export logic for all formats
├── plugin_ui.js     # Frontend export interface
└── README.md        # This file
```

## Learning Points

This example demonstrates:

1. **File Operations**: Creating directories, writing files
2. **External Libraries**: Integrating third-party packages (icalendar)
3. **Multiple Export Formats**: Implementing CSV, JSON, iCal exporters
4. **Datetime Manipulation**: Calculating dates from week numbers
5. **Error Handling**: Graceful handling of missing dependencies
6. **Configuration**: User-customizable export options
7. **Frontend Integration**: Export UI with format selection

## Advanced Features

### CSV Export with Dynamic Columns

```python
header = ['Day', 'Start Time', 'End Time', 'Course']
if self.config.get('include_teacher', True):
    header.append('Teacher')
if self.config.get('include_location', True):
    header.append('Location')
```

### iCal Event Creation

```python
from icalendar import Calendar, Event

cal = Calendar()
event = Event()
event.add('summary', entry.course.name)
event.add('dtstart', datetime.combine(class_date, start_time))
event.add('dtend', datetime.combine(class_date, end_time))
event.add('location', entry.course.location)
cal.add_component(event)
```

### Date Calculation from Week Number

```python
# Calculate week start date
semester_start = datetime.fromisoformat(semester_start_date).date()
week_start = semester_start + timedelta(weeks=week - 1)

# Calculate class date
class_date = week_start + timedelta(days=day - 1)
```

## Troubleshooting

### iCal Export Fails

**Error**: `ImportError: icalendar library required for iCal export`

**Solution**: Install icalendar library:
```bash
pip install icalendar
```

### iCal Export Shows Date Error

**Error**: `ValueError: Semester start date required for iCal export`

**Solution**: Configure semester start date in ClassTop settings

### Export Directory Not Found

The plugin automatically creates the export directory (`~/.classtop/exports/`) if it doesn't exist.

## Extending This Plugin

Ideas for enhancements:

1. **Batch Export**: Export multiple weeks at once
2. **Email Integration**: Email exported schedules
3. **Cloud Upload**: Upload to Google Drive, Dropbox
4. **PDF Export**: Generate PDF schedule with formatting
5. **Excel Format**: Export as .xlsx with formulas and charts
6. **Custom Templates**: User-defined export templates
7. **Scheduled Exports**: Automatic weekly exports

## Related Documentation

- [Python Plugin Development Guide](../../../docs/PYTHON_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [iCalendar Specification (RFC 5545)](https://tools.ietf.org/html/rfc5545)
- [Python icalendar Library](https://icalendar.readthedocs.io/)
