"""
服务器同步客户端
负责与 Classtop-Management-Server 通信
"""

import requests
import threading
import time
import json
import socket
import uuid
from typing import Optional, Dict, List

from . import logger as _logger


class SyncClient:
    """服务器同步客户端"""

    # Valid sync strategies
    VALID_STRATEGIES = {"server_wins", "local_wins", "newest_wins"}

    def __init__(self, settings_manager, schedule_manager):
        self.settings_manager = settings_manager
        self.schedule_manager = schedule_manager
        self.logger = _logger
        self.sync_thread = None
        self.is_running = False
        self.uuid_lock = threading.Lock()  # 用于 UUID 生成的线程锁

    def _validate_strategy(self, strategy: str) -> bool:
        """Validate sync strategy

        Args:
            strategy: Strategy to validate

        Returns:
            True if valid, False otherwise
        """
        return strategy in self.VALID_STRATEGIES

    def _validate_server_url(self, server_url: str) -> bool:
        """Validate server URL uses HTTPS

        Args:
            server_url: Server URL to validate

        Returns:
            True if valid (HTTPS or localhost), False otherwise
        """
        if not server_url:
            return False

        # Allow localhost and 127.0.0.1 for testing
        if "localhost" in server_url or "127.0.0.1" in server_url:
            return True

        # Enforce HTTPS for remote servers
        if not server_url.startswith("https://"):
            self.logger.log_message(
                "error",
                f"Server URL must use HTTPS for security: {server_url}"
            )
            return False

        return True

    def _log_sync_history(self, direction: str, status: str, message: str,
                         courses_synced: int = 0, schedule_synced: int = 0,
                         conflicts_found: int = 0):
        """Log sync operation to history table"""
        try:
            # Use schedule_manager's database connection
            with self.schedule_manager.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO sync_history
                    (direction, status, message, courses_synced, schedule_synced, conflicts_found)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (direction, status, message, courses_synced, schedule_synced, conflicts_found))
                conn.commit()
                self.logger.log_message("debug", f"Sync history logged: {direction} - {status}")
        except Exception as e:
            self.logger.log_message("error", f"Failed to log sync history: {e}")

    def register_client(self) -> bool:
        """向服务器注册客户端"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            if not server_url:
                self.logger.log_message("warning", "未配置服务器地址")
                return False

            # Validate server URL uses HTTPS
            if not self._validate_server_url(server_url):
                return False

            # 获取或生成客户端 UUID（线程安全）
            with self.uuid_lock:
                client_uuid = self.settings_manager.get_setting("client_uuid", "")
                if not client_uuid:
                    client_uuid = str(uuid.uuid4())
                    self.settings_manager.set_setting("client_uuid", client_uuid)

            # 获取客户端名称
            client_name = self.settings_manager.get_setting(
                "client_name", socket.gethostname()
            )

            # 构造注册数据
            data = {
                "uuid": client_uuid,
                "name": client_name,
                "api_url": "",  # 如果启用了客户端 API，填写地址
            }

            # 发送注册请求
            url = f"{server_url.rstrip('/')}/api/clients/register"
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("success"):
                self.logger.log_message(
                    "info", f"客户端注册成功: {client_name}"
                )
                return True
            else:
                self.logger.log_message(
                    "error", f"客户端注册失败: {result}"
                )
                return False

        except Exception as e:
            self.logger.log_message("error", f"注册客户端失败: {e}")
            return False

    def sync_to_server(self) -> bool:
        """同步数据到服务器"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            client_uuid = self.settings_manager.get_setting("client_uuid", "")

            if not server_url or not client_uuid:
                self.logger.log_message(
                    "warning", "服务器地址或客户端 UUID 未配置"
                )
                return False

            # Validate server URL uses HTTPS
            if not self._validate_server_url(server_url):
                return False

            # 获取所有课程
            courses = self.schedule_manager.get_all_courses()

            # 获取所有课程表条目
            schedule_entries = self.schedule_manager.get_all_schedule_entries()

            # 构造同步数据
            sync_data = {
                "client_uuid": client_uuid,
                "courses": [
                    {
                        "id": course["id"],  # 服务器使用 "id" 而不是 "id_on_client"
                        "name": course["name"],
                        "teacher": course.get("teacher"),
                        "color": course.get("color"),
                        "note": course.get("note"),  # 可选字段
                    }
                    for course in courses
                ],
                "schedule_entries": [
                    {
                        "id": entry["id"],  # 服务器使用 "id" 而不是 "id_on_client"
                        "course_id": entry["course_id"],  # 服务器使用 "course_id" 而不是 "course_id_on_client"
                        "day_of_week": entry["day_of_week"],
                        "start_time": entry["start_time"],
                        "end_time": entry["end_time"],
                        "weeks": self._parse_weeks(entry.get("weeks")),
                    }
                    for entry in schedule_entries
                ],
            }

            # 发送同步请求
            url = f"{server_url.rstrip('/')}/api/sync"
            response = requests.post(url, json=sync_data, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("success"):
                sync_info = result.get("data", {})
                # 服务器返回字段: synced_courses, synced_entries
                courses_synced = sync_info.get("synced_courses", 0)
                entries_synced = sync_info.get("synced_entries", 0)
                self.logger.log_message(
                    "info",
                    f"同步成功: {courses_synced} 门课程, {entries_synced} 个课程表条目",
                )

                # Log sync history
                self._log_sync_history(
                    direction="upload",
                    status="success",
                    message=f"同步成功: {courses_synced} 门课程, {entries_synced} 个课程表条目",
                    courses_synced=courses_synced,
                    schedule_synced=entries_synced,
                    conflicts_found=0
                )

                return True
            else:
                error_msg = f"同步失败: {result}"
                self.logger.log_message("error", error_msg)

                # Log failed sync
                self._log_sync_history(
                    direction="upload",
                    status="failure",
                    message=error_msg,
                    courses_synced=0,
                    schedule_synced=0,
                    conflicts_found=0
                )

                return False

        except Exception as e:
            error_msg = f"同步到服务器失败: {e}"
            self.logger.log_message("error", error_msg)

            # Log failed sync
            self._log_sync_history(
                direction="upload",
                status="failure",
                message=error_msg,
                courses_synced=0,
                schedule_synced=0,
                conflicts_found=0
            )

            return False

    def test_connection(self) -> Dict:
        """测试服务器连接"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            if not server_url:
                return {"success": False, "message": "未配置服务器地址"}

            # Validate server URL uses HTTPS
            if not self._validate_server_url(server_url):
                return {"success": False, "message": "服务器地址必须使用HTTPS协议"}

            url = f"{server_url.rstrip('/')}/api/health"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            result = response.json()
            if result.get("success"):
                return {
                    "success": True,
                    "message": "连接成功",
                    "data": result.get("data"),
                }
            else:
                return {"success": False, "message": "服务器响应异常"}

        except requests.exceptions.Timeout:
            return {"success": False, "message": "连接超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "无法连接到服务器"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}

    def start_auto_sync(self):
        """启动自动同步（后台线程）"""
        sync_enabled = self.settings_manager.get_setting_bool("sync_enabled", False)
        if not sync_enabled:
            self.logger.log_message("info", "同步功能未启用")
            return

        if self.is_running:
            self.logger.log_message("warning", "同步线程已在运行")
            return

        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.log_message("info", "启动自动同步线程")

    def stop_auto_sync(self):
        """停止自动同步"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.logger.log_message("info", "停止自动同步线程")

    def _sync_loop(self):
        """同步循环"""
        while self.is_running:
            try:
                interval = int(
                    self.settings_manager.get_setting("sync_interval", "300")
                )

                # 获取同步方向设置
                sync_direction = self.settings_manager.get_setting("sync_direction", "upload")

                # 根据同步方向执行对应的同步操作
                if sync_direction == "bidirectional":
                    sync_strategy = self.settings_manager.get_setting("sync_strategy", "server_wins")
                    result = self.bidirectional_sync(strategy=sync_strategy)
                    success = result.get("success", False)
                    if success:
                        self.logger.log_message(
                            "info",
                            f"双向同步成功: {result.get('courses_updated', 0)} 门课程, "
                            f"{result.get('entries_updated', 0)} 个课程表条目, "
                            f"{result.get('conflicts_found', 0)} 个冲突, "
                            f"等待 {interval} 秒"
                        )
                    else:
                        self.logger.log_message("error", f"双向同步失败: {result.get('message')}")
                elif sync_direction == "download":
                    result = self.download_from_server()
                    success = result.get("success", False)
                    if success:
                        # 应用下载的数据
                        apply_success = self.apply_server_data(result)
                        if apply_success:
                            self.logger.log_message(
                                "info", f"下载同步成功，等待 {interval} 秒"
                            )
                        else:
                            self.logger.log_message("error", "应用服务器数据失败")
                            success = False
                    else:
                        self.logger.log_message("error", f"下载同步失败: {result.get('message')}")
                else:  # upload (default)
                    success = self.sync_to_server()
                    if success:
                        self.logger.log_message(
                            "info", f"上传同步成功，等待 {interval} 秒"
                        )
                    else:
                        self.logger.log_message("error", "上传同步失败，将在下次重试")

                # 等待指定间隔
                for _ in range(interval):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.log_message("error", f"同步循环异常: {e}")
                time.sleep(60)  # 出错后等待 1 分钟

    def download_from_server(self) -> Dict:
        """Download data from server

        Returns:
            Dict with keys:
            - success: bool
            - message: str
            - courses: List[Dict] (if successful)
            - schedule_entries: List[Dict] (if successful)
        """
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            client_uuid = self.settings_manager.get_setting("client_uuid", "")

            if not server_url or not client_uuid:
                return {
                    "success": False,
                    "message": "服务器地址或客户端 UUID 未配置"
                }

            # Validate server URL uses HTTPS
            if not self._validate_server_url(server_url):
                return {
                    "success": False,
                    "message": "服务器地址必须使用HTTPS协议"
                }

            self.logger.log_message("info", f"从服务器下载数据: {client_uuid}")

            # Download courses
            courses_url = f"{server_url.rstrip('/')}/api/clients/{client_uuid}/courses"
            courses_response = requests.get(courses_url, timeout=30)
            courses_response.raise_for_status()
            courses_result = courses_response.json()

            if not courses_result.get("success"):
                return {
                    "success": False,
                    "message": f"下载课程失败: {courses_result.get('message', '未知错误')}"
                }

            # Download schedule entries
            schedule_url = f"{server_url.rstrip('/')}/api/clients/{client_uuid}/schedule"
            schedule_response = requests.get(schedule_url, timeout=30)
            schedule_response.raise_for_status()
            schedule_result = schedule_response.json()

            if not schedule_result.get("success"):
                return {
                    "success": False,
                    "message": f"下载课程表失败: {schedule_result.get('message', '未知错误')}"
                }

            courses = courses_result.get("data", {}).get("courses", [])
            schedule_entries = schedule_result.get("data", {}).get("schedule_entries", [])

            self.logger.log_message(
                "info",
                f"下载成功: {len(courses)} 门课程, {len(schedule_entries)} 个课程表条目"
            )

            # Log download success
            self._log_sync_history(
                direction="download",
                status="success",
                message=f"下载成功: {len(courses)} 门课程, {len(schedule_entries)} 个课程表条目",
                courses_synced=len(courses),
                schedule_synced=len(schedule_entries),
                conflicts_found=0
            )

            return {
                "success": True,
                "message": "下载成功",
                "courses": courses,
                "schedule_entries": schedule_entries
            }

        except requests.exceptions.Timeout:
            error_msg = "连接超时"
            self._log_sync_history(
                direction="download",
                status="failure",
                message=error_msg,
                courses_synced=0,
                schedule_synced=0,
                conflicts_found=0
            )
            return {"success": False, "message": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "无法连接到服务器"
            self._log_sync_history(
                direction="download",
                status="failure",
                message=error_msg,
                courses_synced=0,
                schedule_synced=0,
                conflicts_found=0
            )
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            self.logger.log_message("error", f"从服务器下载数据失败: {e}")
            self._log_sync_history(
                direction="download",
                status="failure",
                message=error_msg,
                courses_synced=0,
                schedule_synced=0,
                conflicts_found=0
            )
            return {"success": False, "message": error_msg}

    def detect_conflicts(self, local_data: Dict, server_data: Dict) -> Dict:
        """Detect conflicts between local and server data

        Args:
            local_data: {"courses": [...], "schedule_entries": [...]}
            server_data: {"courses": [...], "schedule_entries": [...]}

        Returns:
            Dict with:
            - has_conflicts: bool
            - conflicted_courses: List[Dict]  # {local: {...}, server: {...}}
            - conflicted_entries: List[Dict]  # {local: {...}, server: {...}}
        """
        try:
            self.logger.log_message("info", "检测数据冲突")

            conflicted_courses = []
            conflicted_entries = []

            # Build maps for quick lookup
            local_courses_map = {c["id"]: c for c in local_data.get("courses", [])}
            server_courses_map = {c["id"]: c for c in server_data.get("courses", [])}

            # Check course conflicts
            for course_id, local_course in local_courses_map.items():
                if course_id in server_courses_map:
                    server_course = server_courses_map[course_id]
                    # Compare relevant fields
                    if (local_course.get("name") != server_course.get("name") or
                        local_course.get("teacher") != server_course.get("teacher") or
                        local_course.get("location") != server_course.get("location") or
                        local_course.get("color") != server_course.get("color")):

                        conflicted_courses.append({
                            "id": course_id,
                            "local": local_course,
                            "server": server_course
                        })

            # Build maps for schedule entries
            local_entries_map = {e["id"]: e for e in local_data.get("schedule_entries", [])}
            server_entries_map = {e["id"]: e for e in server_data.get("schedule_entries", [])}

            # Check schedule entry conflicts
            for entry_id, local_entry in local_entries_map.items():
                if entry_id in server_entries_map:
                    server_entry = server_entries_map[entry_id]
                    # Compare relevant fields
                    local_weeks = self._parse_weeks(local_entry.get("weeks"))
                    server_weeks = server_entry.get("weeks", [])

                    if (local_entry.get("course_id") != server_entry.get("course_id") or
                        local_entry.get("day_of_week") != server_entry.get("day_of_week") or
                        local_entry.get("start_time") != server_entry.get("start_time") or
                        local_entry.get("end_time") != server_entry.get("end_time") or
                        local_weeks != server_weeks):

                        conflicted_entries.append({
                            "id": entry_id,
                            "local": local_entry,
                            "server": server_entry
                        })

            has_conflicts = len(conflicted_courses) > 0 or len(conflicted_entries) > 0

            self.logger.log_message(
                "info",
                f"冲突检测完成: {len(conflicted_courses)} 门课程冲突, "
                f"{len(conflicted_entries)} 个课程表条目冲突"
            )

            return {
                "has_conflicts": has_conflicts,
                "conflicted_courses": conflicted_courses,
                "conflicted_entries": conflicted_entries
            }

        except Exception as e:
            self.logger.log_message("error", f"检测冲突失败: {e}")
            return {
                "has_conflicts": False,
                "conflicted_courses": [],
                "conflicted_entries": []
            }

    def merge_data(self, local_data: Dict, server_data: Dict, strategy: str = "server_wins") -> Dict:
        """Merge local and server data

        Args:
            local_data: Local courses and schedule
            server_data: Server courses and schedule
            strategy: "server_wins", "local_wins", or "newest_wins"

        Returns:
            Merged data dict with:
            - courses: List[Dict]
            - schedule_entries: List[Dict]
        """
        try:
            # Validate strategy
            if not self._validate_strategy(strategy):
                self.logger.log_message(
                    "warning",
                    f"Invalid strategy '{strategy}', using 'server_wins' instead. "
                    f"Valid strategies: {', '.join(self.VALID_STRATEGIES)}"
                )
                strategy = "server_wins"

            self.logger.log_message("info", f"合并数据，策略: {strategy}")

            local_courses = local_data.get("courses", [])
            server_courses = server_data.get("courses", [])
            local_entries = local_data.get("schedule_entries", [])
            server_entries = server_data.get("schedule_entries", [])

            # Build maps
            local_courses_map = {c["id"]: c for c in local_courses}
            server_courses_map = {c["id"]: c for c in server_courses}
            local_entries_map = {e["id"]: e for e in local_entries}
            server_entries_map = {e["id"]: e for e in server_entries}

            merged_courses = {}
            merged_entries = {}

            # Merge courses based on strategy
            if strategy == "server_wins":
                # Start with local, then override with server
                merged_courses = {**local_courses_map, **server_courses_map}
            elif strategy == "local_wins":
                # Start with server, then override with local
                merged_courses = {**server_courses_map, **local_courses_map}
            elif strategy == "newest_wins":
                # For now, use server_wins as we don't have timestamps
                # TODO: Implement timestamp-based merging when available
                self.logger.log_message("warning", "newest_wins 策略未实现，使用 server_wins 替代")
                merged_courses = {**local_courses_map, **server_courses_map}
            else:
                self.logger.log_message("warning", f"未知策略 {strategy}，使用 server_wins 替代")
                merged_courses = {**local_courses_map, **server_courses_map}

            # Merge schedule entries with same strategy
            if strategy == "server_wins":
                merged_entries = {**local_entries_map, **server_entries_map}
            elif strategy == "local_wins":
                merged_entries = {**server_entries_map, **local_entries_map}
            elif strategy == "newest_wins":
                self.logger.log_message("warning", "newest_wins 策略未实现，使用 server_wins 替代")
                merged_entries = {**local_entries_map, **server_entries_map}
            else:
                merged_entries = {**local_entries_map, **server_entries_map}

            result = {
                "courses": list(merged_courses.values()),
                "schedule_entries": list(merged_entries.values())
            }

            self.logger.log_message(
                "info",
                f"数据合并完成: {len(result['courses'])} 门课程, "
                f"{len(result['schedule_entries'])} 个课程表条目"
            )

            return result

        except Exception as e:
            self.logger.log_message("error", f"合并数据失败: {e}")
            # Return local data as fallback
            return {
                "courses": local_data.get("courses", []),
                "schedule_entries": local_data.get("schedule_entries", [])
            }

    def apply_server_data(self, server_data: Dict) -> bool:
        """Apply server data to local database

        Updates local courses and schedule entries with server data.
        Uses schedule_manager's update_course() and add_schedule_entry() methods.

        Args:
            server_data: Dict with "courses" and "schedule_entries" keys

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.log_message("info", "应用服务器数据到本地数据库")

            courses = server_data.get("courses", [])
            schedule_entries = server_data.get("schedule_entries", [])

            courses_updated = 0
            entries_updated = 0

            # Get existing local courses and entries for reference
            local_courses = {c["id"]: c for c in self.schedule_manager.get_all_courses()}
            local_entries = {e["id"]: e for e in self.schedule_manager.get_all_schedule_entries()}

            # Update or add courses
            for course in courses:
                course_id = course.get("id")
                if not course_id:
                    continue

                if course_id in local_courses:
                    # Update existing course
                    success = self.schedule_manager.update_course(
                        course_id=course_id,
                        name=course.get("name"),
                        teacher=course.get("teacher"),
                        location=course.get("location"),
                        color=course.get("color")
                    )
                    if success:
                        courses_updated += 1
                else:
                    # Add new course (note: this will create a new ID, need special handling)
                    # For now, we'll skip adding courses that don't exist locally
                    # This should be handled by proper sync logic
                    self.logger.log_message(
                        "warning",
                        f"课程 ID {course_id} 在本地不存在，跳过"
                    )

            # Update or add schedule entries
            for entry in schedule_entries:
                entry_id = entry.get("id")
                if not entry_id:
                    continue

                # Parse weeks data
                weeks = entry.get("weeks", [])
                if isinstance(weeks, str):
                    weeks = self._parse_weeks(weeks)

                if entry_id in local_entries:
                    # Delete and re-add (simpler than update for schedule entries)
                    self.schedule_manager.delete_schedule_entry(entry_id)
                    new_id = self.schedule_manager.add_schedule_entry(
                        course_id=entry.get("course_id"),
                        day_of_week=entry.get("day_of_week"),
                        start_time=entry.get("start_time"),
                        end_time=entry.get("end_time"),
                        weeks=weeks,
                        note=entry.get("note")
                    )
                    if new_id > 0:
                        entries_updated += 1
                else:
                    # Add new entry
                    new_id = self.schedule_manager.add_schedule_entry(
                        course_id=entry.get("course_id"),
                        day_of_week=entry.get("day_of_week"),
                        start_time=entry.get("start_time"),
                        end_time=entry.get("end_time"),
                        weeks=weeks,
                        note=entry.get("note")
                    )
                    if new_id > 0:
                        entries_updated += 1

            self.logger.log_message(
                "info",
                f"服务器数据应用完成: {courses_updated} 门课程更新, "
                f"{entries_updated} 个课程表条目更新"
            )

            return True

        except Exception as e:
            self.logger.log_message("error", f"应用服务器数据失败: {e}")
            return False

    def bidirectional_sync(self, strategy: str = "server_wins") -> Dict:
        """Perform bidirectional sync with conflict resolution

        Args:
            strategy: "server_wins", "local_wins", or "newest_wins"

        Returns:
            Dict with sync result:
            - success: bool
            - message: str
            - conflicts_found: int
            - courses_updated: int
            - entries_updated: int
        """
        try:
            # Validate strategy
            if not self._validate_strategy(strategy):
                return {
                    "success": False,
                    "message": f"Invalid sync strategy '{strategy}'. Valid strategies: {', '.join(self.VALID_STRATEGIES)}",
                    "conflicts_found": 0,
                    "courses_updated": 0,
                    "entries_updated": 0
                }

            self.logger.log_message("info", f"开始双向同步，策略: {strategy}")

            # Step 1: Download from server
            download_result = self.download_from_server()
            if not download_result.get("success"):
                return {
                    "success": False,
                    "message": f"下载失败: {download_result.get('message')}",
                    "conflicts_found": 0,
                    "courses_updated": 0,
                    "entries_updated": 0
                }

            server_data = {
                "courses": download_result.get("courses", []),
                "schedule_entries": download_result.get("schedule_entries", [])
            }

            # Step 2: Get local data
            local_data = {
                "courses": self.schedule_manager.get_all_courses(),
                "schedule_entries": self.schedule_manager.get_all_schedule_entries()
            }

            # Step 3: Detect conflicts
            conflict_result = self.detect_conflicts(local_data, server_data)
            conflicts_found = (
                len(conflict_result.get("conflicted_courses", [])) +
                len(conflict_result.get("conflicted_entries", []))
            )

            if conflicts_found > 0:
                self.logger.log_message("info", f"发现 {conflicts_found} 个冲突，应用策略: {strategy}")

            # Step 4: Merge data according to strategy
            merged_data = self.merge_data(local_data, server_data, strategy)

            # Step 5: Apply merged data locally
            apply_success = self.apply_server_data(merged_data)
            if not apply_success:
                return {
                    "success": False,
                    "message": "应用合并数据到本地失败",
                    "conflicts_found": conflicts_found,
                    "courses_updated": 0,
                    "entries_updated": 0
                }

            # Step 6: Upload final data to server
            upload_success = self.sync_to_server()
            if not upload_success:
                return {
                    "success": False,
                    "message": "上传合并数据到服务器失败",
                    "conflicts_found": conflicts_found,
                    "courses_updated": len(merged_data.get("courses", [])),
                    "entries_updated": len(merged_data.get("schedule_entries", []))
                }

            # Step 7: Return detailed result
            result = {
                "success": True,
                "message": "双向同步成功",
                "conflicts_found": conflicts_found,
                "courses_updated": len(merged_data.get("courses", [])),
                "entries_updated": len(merged_data.get("schedule_entries", []))
            }

            self.logger.log_message(
                "info",
                f"双向同步完成: {result['courses_updated']} 门课程, "
                f"{result['entries_updated']} 个课程表条目, "
                f"{result['conflicts_found']} 个冲突已解决"
            )

            # Log bidirectional sync with conflict status
            sync_status = "conflict" if conflicts_found > 0 else "success"
            self._log_sync_history(
                direction="bidirectional",
                status=sync_status,
                message=f"双向同步完成: {result['courses_updated']} 门课程, {result['entries_updated']} 个课程表条目, {result['conflicts_found']} 个冲突已解决",
                courses_synced=result['courses_updated'],
                schedule_synced=result['entries_updated'],
                conflicts_found=conflicts_found
            )

            return result

        except Exception as e:
            error_msg = f"同步异常: {str(e)}"
            self.logger.log_message("error", f"双向同步失败: {e}")

            # Log failed bidirectional sync
            self._log_sync_history(
                direction="bidirectional",
                status="failure",
                message=error_msg,
                courses_synced=0,
                schedule_synced=0,
                conflicts_found=0
            )

            return {
                "success": False,
                "message": error_msg,
                "conflicts_found": 0,
                "courses_updated": 0,
                "entries_updated": 0
            }

    def _parse_weeks(self, weeks_data: Optional[str]) -> List[int]:
        """安全解析 weeks JSON 数据

        Args:
            weeks_data: JSON 字符串或 None

        Returns:
            周次列表，解析失败时返回空列表
        """
        if not weeks_data:
            return []

        try:
            weeks = json.loads(weeks_data)
            # 确保返回值是列表且所有元素都是整数
            if isinstance(weeks, list):
                return [int(w) for w in weeks if isinstance(w, (int, str)) and str(w).isdigit()]
            return []
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            self.logger.log_message("warning", f"解析 weeks 数据失败: {e}, 数据: {weeks_data}")
            return []
