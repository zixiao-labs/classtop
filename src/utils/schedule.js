import { pyInvoke } from 'tauri-plugin-pytauri-api';

// 星期映射
export const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

// 颜色预设
export const courseColors = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA5E9', '#6C5CE7', '#A29BFE', '#FD79A8', '#FDCB6E',
  '#6C63FF', '#00B8A9', '#F8B500', '#F53B57', '#3C40C6'
];

/**
 * 格式化时间 HH:MM
 */
export function formatTime(hour, minute) {
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
}

/**
 * 解析时间字符串
 */
export function parseTime(timeStr) {
  const [hour, minute] = timeStr.split(':').map(Number);
  return { hour, minute };
}

/**
 * 计算时间差（分钟）
 */
export function getTimeDiff(startTime, endTime) {
  const start = parseTime(startTime);
  const end = parseTime(endTime);
  return (end.hour - start.hour) * 60 + (end.minute - start.minute);
}

/**
 * 生成时间段数组
 */
export function generateTimeSlots(startHour = 8, endHour = 22, interval = 60) {
  const slots = [];
  for (let hour = startHour; hour < endHour; hour++) {
    slots.push({
      time: formatTime(hour, 0),
      label: `${hour}:00`
    });
  }
  return slots;
}

/**
 * 获取当前周数信息（计算或手动）
 */
export async function getCurrentWeekInfo() {
  try {
    const info = await pyInvoke('get_current_week');
    return info;
  } catch (error) {
    console.error('Failed to get current week info:', error);
    return { week: 1, semester_start_date: '', is_calculated: false };
  }
}

/**
 * 设置学期开始日期用于自动计算周数
 */
export async function setSemesterStartDate(date) {
  try {
    const result = await pyInvoke('set_semester_start_date', { date });
    return result;
  } catch (error) {
    console.error('Failed to set semester start date:', error);
    return { success: false };
  }
}

/**
 * 获取当前周数
 */
export async function getCurrentWeek() {
  try {
    const info = await pyInvoke('get_current_week');
    return info.week;
  } catch (error) {
    console.error('Failed to get current week:', error);
    return 1;
  }
}

/**
 * 获取所有课程
 */
export async function getCourses() {
  try {
    const courses = await pyInvoke('get_courses');
    return courses;
  } catch (error) {
    console.error('Failed to get courses:', error);
    return [];
  }
}

/**
 * 添加课程
 */
export async function addCourse(course) {
  try {
    const result = await pyInvoke('add_course', course);
    return result;
  } catch (error) {
    console.error('Failed to add course:', error);
    throw error;
  }
}

/**
 * 更新课程信息
 */
export async function updateCourse(courseId, courseData) {
  try {
    const result = await pyInvoke('update_course', { id: courseId, ...courseData });
    return result;
  } catch (error) {
    console.error('Failed to update course:', error);
    throw error;
  }
}

/**
 * 删除课程
 */
export async function deleteCourse(courseId) {
  try {
    const result = await pyInvoke('delete_course', { id: courseId });
    return result.success;
  } catch (error) {
    console.error('Failed to delete course:', error);
    return false;
  }
}

/**
 * 获取课程表
 */
export async function getSchedule(week = null) {
  try {
    const schedule = await pyInvoke('get_schedule', { week });
    return schedule;
  } catch (error) {
    console.error('Failed to get schedule:', error);
    return [];
  }
}

/**
 * 添加课程表项
 */
export async function addScheduleEntry(entry) {
  try {
    const result = await pyInvoke('add_schedule_entry', entry);
    return result;
  } catch (error) {
    console.error('Failed to add schedule entry:', error);
    throw error;
  }
}

/**
 * 删除课程表项
 */
export async function deleteScheduleEntry(entryId) {
  try {
    const result = await pyInvoke('delete_schedule_entry', { id: entryId });
    return result.success;
  } catch (error) {
    console.error('Failed to delete schedule entry:', error);
    return false;
  }
}

/**
 * 获取当前课程
 * DEPRECATED: Use getScheduleByDay + findCurrentClass
 */
export async function getCurrentClass() {
  try {
    const currentClass = await pyInvoke('get_current_class');
    return currentClass;
  } catch (error) {
    console.error('Failed to get current class:', error);
    return null;
  }
}

/**
 * 获取下一节课
 * DEPRECATED: Use getScheduleByDay + findNextClass
 */
export async function getNextClass() {
  try {
    const nextClass = await pyInvoke('get_next_class');
    return nextClass;
  } catch (error) {
    console.error('Failed to get next class:', error);
    return null;
  }
}

/**
 * 获取刚结束的上一节课
 * DEPRECATED: Use getScheduleByDay + findLastClass
 */
export async function getLastClass() {
  try {
    const lastClass = await pyInvoke('get_last_class');
    return lastClass;
  } catch (error) {
    console.error('Failed to get last class:', error);
    return null;
  }
}

/**
 * 获取某天的课程表
 */
export async function getScheduleByDay(dayOfWeek, week = null) {
  try {
    const schedule = await pyInvoke('get_schedule_by_day', { day_of_week: dayOfWeek, week });
    return schedule || [];
  } catch (error) {
    console.error('Failed to get schedule by day:', error);
    return [];
  }
}

/**
 * 获取整周的课程表
 */
export async function getScheduleForWeek(week = null) {
  try {
    const schedule = await pyInvoke('get_schedule_for_week', { week });
    return schedule || [];
  } catch (error) {
    console.error('Failed to get schedule for week:', error);
    return [];
  }
}

/**
 * 从课程列表中查找当前正在上的课
 */
export function findCurrentClass(classes, currentTime = null) {
  if (!classes || classes.length === 0) return null;

  const now = currentTime || new Date();
  const timeStr = formatTime(now.getHours(), now.getMinutes());

  for (const cls of classes) {
    if (cls.start_time <= timeStr && cls.end_time > timeStr) {
      return cls;
    }
  }

  return null;
}

/**
 * 从课程列表中查找下一节课
 */
export function findNextClass(classes, currentTime = null) {
  if (!classes || classes.length === 0) return null;

  const now = currentTime || new Date();
  const timeStr = formatTime(now.getHours(), now.getMinutes());

  // Find next class in current day
  for (const cls of classes) {
    if (cls.start_time > timeStr) {
      return cls;
    }
  }

  return null;
}

/**
 * 从课程列表中查找刚结束的上一节课
 */
export function findLastClass(classes, currentTime = null) {
  if (!classes || classes.length === 0) return null;

  const now = currentTime || new Date();
  const timeStr = formatTime(now.getHours(), now.getMinutes());

  let lastClass = null;

  // Find the most recent ended class
  for (const cls of classes) {
    if (cls.end_time <= timeStr) {
      lastClass = cls;
    } else {
      break; // Classes are sorted by start_time, so we can break
    }
  }

  return lastClass;
}

/**
 * 从整周课程中查找跨天的下一节课
 */
export function findNextClassAcrossWeek(weekSchedule, currentDayOfWeek, currentTime = null) {
  if (!weekSchedule || weekSchedule.length === 0) return null;

  const now = currentTime || new Date();
  const timeStr = formatTime(now.getHours(), now.getMinutes());

  // First, check today's remaining classes
  const todayClasses = weekSchedule.filter(cls => cls.day_of_week === currentDayOfWeek);
  const nextToday = findNextClass(todayClasses, currentTime);
  if (nextToday) return nextToday;

  // Then check the following days
  for (let offset = 1; offset < 7; offset++) {
    const targetDay = ((currentDayOfWeek - 1 + offset) % 7) + 1;
    const dayClasses = weekSchedule.filter(cls => cls.day_of_week === targetDay);

    if (dayClasses.length > 0) {
      // Return the first class of that day (already sorted by time)
      return dayClasses[0];
    }
  }

  return null;
}

/**
 * 按天分组课程表
 */
export function groupScheduleByDay(schedule) {
  const grouped = {};
  for (let day = 1; day <= 7; day++) {
    grouped[day] = [];
  }

  schedule.forEach(item => {
    if (grouped[item.day_of_week]) {
      grouped[item.day_of_week].push(item);
    }
  });

  // 排序每天的课程
  Object.keys(grouped).forEach(day => {
    grouped[day].sort((a, b) => {
      const timeA = parseTime(a.start_time);
      const timeB = parseTime(b.start_time);
      return timeA.hour * 60 + timeA.minute - (timeB.hour * 60 + timeB.minute);
    });
  });

  return grouped;
}

/**
 * 计算课程在网格中的位置
 */
export function calculateCoursePosition(startTime, endTime, gridStartHour = 8, hourHeight = 60) {
  const start = parseTime(startTime);
  const end = parseTime(endTime);

  const top = ((start.hour - gridStartHour) * 60 + start.minute) * (hourHeight / 60);
  const height = ((end.hour - start.hour) * 60 + (end.minute - start.minute)) * (hourHeight / 60);

  return { top, height };
}

/**
 * 生成周数选择器选项
 */
export function generateWeekOptions(totalWeeks = 20) {
  return Array.from({ length: totalWeeks }, (_, i) => ({
    value: i + 1,
    label: `第${i + 1}周`
  }));
}

/**
 * 获取今天是星期几（1-7）
 */
export function getTodayWeekday() {
  const day = new Date().getDay();
  return day === 0 ? 7 : day;
}

/**
 * 计算课程进度
 */
export function calculateCourseProgress(startTime, endTime, currentTime = null) {
  const now = currentTime || new Date();

  // 解析时间
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);

  const currentHour = now.getHours();
  const currentMin = now.getMinutes();
  const currentSec = now.getSeconds();

  // 转换为总秒数
  const startSeconds = startHour * 3600 + startMin * 60;
  const endSeconds = endHour * 3600 + endMin * 60;
  const currentSeconds = currentHour * 3600 + currentMin * 60 + currentSec;

  if (currentSeconds < startSeconds) {
    return 0;
  } else if (currentSeconds >= endSeconds) {
    return 1;
  } else {
    return (currentSeconds - startSeconds) / (endSeconds - startSeconds);
  }
}

/**
 * 检查是否为当前时间段
 */
export function isCurrentTimeSlot(startTime, endTime) {
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();

  const start = parseTime(startTime);
  const end = parseTime(endTime);

  const startMinutes = start.hour * 60 + start.minute;
  const endMinutes = end.hour * 60 + end.minute;

  return currentMinutes >= startMinutes && currentMinutes < endMinutes;
}

/**
 * 检查课程时间冲突
 */
export async function checkScheduleConflict(dayOfWeek, startTime, endTime, weeks = null, excludeEntryId = null) {
  try {
    const result = await pyInvoke('check_schedule_conflict', {
      day_of_week: dayOfWeek,
      start_time: startTime,
      end_time: endTime,
      weeks,
      exclude_entry_id: excludeEntryId
    });
    return result;
  } catch (error) {
    console.error('Failed to check schedule conflict:', error);
    return { has_conflict: false, conflicts: [] };
  }
}

/**
 * 导出课程表数据
 */
export async function exportScheduleData(format = 'json', includeCourses = true, includeSchedule = true, includeSettings = false) {
  try {
    const result = await pyInvoke('export_schedule_data', {
      format,
      include_courses: includeCourses,
      include_schedule: includeSchedule,
      include_settings: includeSettings
    });
    return result;
  } catch (error) {
    console.error('Failed to export schedule data:', error);
    return { success: false, message: '导出失败', data: null };
  }
}

/**
 * 导入课程表数据
 */
export async function importScheduleData(format, data, replaceExisting = false) {
  try {
    const result = await pyInvoke('import_schedule_data', {
      format,
      data,
      replace_existing: replaceExisting
    });
    return result;
  } catch (error) {
    console.error('Failed to import schedule data:', error);
    return { success: false, message: '导入失败', courses_imported: 0, schedule_imported: 0 };
  }
}

/**
 * 从GitHub下载随机主题图片
 */
export async function downloadRandomThemeImage() {
  try {
    const result = await pyInvoke('download_random_theme_image');
    return result;
  } catch (error) {
    console.error('Failed to download theme image:', error);
    return { success: false, message: '下载失败' };
  }
}