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

    def __init__(self, settings_manager, schedule_manager):
        self.settings_manager = settings_manager
        self.schedule_manager = schedule_manager
        self.logger = _logger
        self.sync_thread = None
        self.is_running = False
        self.uuid_lock = threading.Lock()  # 用于 UUID 生成的线程锁

    def register_client(self) -> bool:
        """向服务器注册客户端"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            if not server_url:
                self.logger.log_message("warning", "未配置服务器地址")
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
                return True
            else:
                self.logger.log_message("error", f"同步失败: {result}")
                return False

        except Exception as e:
            self.logger.log_message("error", f"同步到服务器失败: {e}")
            return False

    def test_connection(self) -> Dict:
        """测试服务器连接"""
        try:
            server_url = self.settings_manager.get_setting("server_url", "")
            if not server_url:
                return {"success": False, "message": "未配置服务器地址"}

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

                # 执行同步
                success = self.sync_to_server()
                if success:
                    self.logger.log_message(
                        "info", f"同步成功，等待 {interval} 秒"
                    )
                else:
                    self.logger.log_message("error", "同步失败，将在下次重试")

                # 等待指定间隔
                for _ in range(interval):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.log_message("error", f"同步循环异常: {e}")
                time.sleep(60)  # 出错后等待 1 分钟

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
