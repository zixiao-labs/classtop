"""
麦克风监控器
"""

import sounddevice as sd
import time
from .core import AudioMonitor, AudioLevel
from threading import Thread
from .. import _logger


class MicrophoneMonitor(AudioMonitor):
    """麦克风（外界音量）监控器"""

    def start(self):
        """启动麦克风监控"""
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _audio_callback(self, indata, frames, time_info, status):
        """音频输入回调"""
        if status:
            _logger.log_message("info", f"Microphone status: {status}")

        # 计算响度
        audio_data = indata[:, 0] if self.channels > 1 else indata.flatten()
        level = self._calculate_level(audio_data)

        # 更新当前数据
        self.current_level = level

        # 通知回调
        self._notify_callbacks(level)

    def _monitor_loop(self):
        """监控循环"""
        try:
            with sd.InputStream(
                device=self.device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self._audio_callback
            ):
                while self.is_running and not self._stop_event.is_set():
                    time.sleep(0.1)
        except Exception as e:
            _logger.log_message("error", f"Microphone monitoring error: {e}")
            self.is_running = False