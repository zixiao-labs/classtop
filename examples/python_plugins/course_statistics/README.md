# Course Statistics Plugin

An advanced example plugin that demonstrates data analysis, background tasks, and frontend integration.

## Features

- ✅ Real-time course and schedule statistics
- ✅ Background periodic updates
- ✅ Data aggregation and analysis
- ✅ Event-driven architecture
- ✅ Frontend dashboard with Vue.js
- ✅ Configuration management
- ✅ State persistence

## Installation

1. Copy this directory to your ClassTop plugins folder:

```bash
cp -r course_statistics ~/.classtop/plugins/
```

2. Restart ClassTop or reload plugins

3. Enable the plugin in Settings → Plugin Management

## What This Plugin Does

This plugin automatically analyzes your course data and provides insights:

### Statistics Calculated

1. **Total Courses**: Number of courses in the system
2. **Courses by Teacher**: Distribution of courses per teacher
3. **Courses by Location**: Distribution of courses per classroom
4. **Schedule Entries per Day**: Classes scheduled for each day
5. **Total Class Hours**: Hours of class per week
6. **Busiest Day**: Day with most classes

### Background Tasks

- Automatically recalculates statistics every 5 minutes (configurable)
- Immediately updates when courses or schedules change
- Emits `statistics_updated` event after each calculation

### Frontend Dashboard

Access the statistics dashboard in Settings → Plugin Management → Course Statistics.

The dashboard shows:
- Summary cards with key metrics
- Teacher distribution list
- Location distribution list
- Configuration options
- Manual refresh button

## Configuration

Customize the plugin behavior:

- **Update Interval**: How often to recalculate statistics (60-3600 seconds)
- **Enable Notifications**: Whether to show notifications on updates
- **Min Class Hours**: Minimum hours to trigger alerts (future feature)

Configuration is saved automatically and persists across restarts.

## Events

### Subscribed Events

- `course_update`: Triggers recalculation when courses change
- `schedule_update`: Triggers recalculation when schedules change

### Emitted Events

#### `statistics_updated`
```json
{
  "total_courses": 10,
  "courses_by_teacher": {
    "Prof. Smith": 3,
    "Dr. Johnson": 2
  },
  "courses_by_location": {
    "A101": 5,
    "B202": 3
  },
  "schedule_entries_per_day": {
    "1": 3,
    "2": 2,
    "3": 4
  },
  "total_class_hours": 24.5,
  "busiest_day": 3,
  "timestamp": "2025-11-01T10:30:00"
}
```

## Code Structure

```
course_statistics/
├── plugin.yaml      # Plugin metadata with frontend component
├── plugin.py        # Backend logic (analysis, background tasks)
├── plugin_ui.js     # Frontend dashboard component
└── README.md        # This file
```

## Learning Points

This example demonstrates:

1. **Background Tasks**: Using `asyncio.create_task()` for periodic operations
2. **Event Handling**: Subscribing to system events and emitting custom events
3. **Configuration Management**: Loading, saving, and validating plugin config
4. **Frontend Integration**: Creating Vue.js dashboard in settings page
5. **Data Analysis**: Aggregating and processing course/schedule data
6. **State Management**: Saving background task state for hot reload
7. **Error Handling**: Graceful degradation and logging

## Advanced Features

### Async Background Tasks

```python
async def periodic_update(self):
    """Background task for periodic statistics updates"""
    while True:
        try:
            await asyncio.sleep(self.update_interval)
            await self.analyze_statistics()
        except asyncio.CancelledError:
            break
```

### Data Aggregation

```python
from collections import defaultdict

stats["courses_by_teacher"] = defaultdict(int)
for course in courses:
    stats["courses_by_teacher"][course.teacher] += 1
```

### Frontend-Backend Communication

```javascript
// Frontend calls backend
await this.$classtop.plugins.invoke('com.example.course_statistics', 'refresh_statistics');

// Frontend receives backend events
this.$classtop.plugins.on('statistics_updated', this.onStatisticsUpdate);
```

## Extending This Plugin

Ideas for enhancements:

1. **Charts**: Add chart.js or echarts for visual data representation
2. **Export**: Export statistics to CSV/JSON files
3. **Alerts**: Notify when class hours exceed threshold
4. **History**: Track statistics over time
5. **Comparison**: Compare different weeks/semesters

## Related Documentation

- [Python Plugin Development Guide](../../../docs/PYTHON_PLUGIN_GUIDE.md)
- [Plugin IPC Specification](../../../docs/PLUGIN_IPC_SPECIFICATION.md)
- [Vue.js Component Guide](https://vuejs.org/guide/components.html)
- [MDUI Components](https://www.mdui.org/en/docs/2/)
