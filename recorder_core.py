import subprocess
import os
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable


class Recorder:
    def __init__(self, output_dir: str = "recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process: Optional[subprocess.Popen] = None
        self.is_recording = False
        self.start_time: Optional[datetime] = None
        self.platform = ""
        self.room_id = ""
        self.streamer_name = ""
        self.output_file = ""
        self.tool = self._detect_tool()

    def _detect_tool(self) -> str:
        tools = ["streamlink", "yt-dlp", "ffmpeg"]
        for tool in tools:
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    return tool
            except:
                continue
        return ""

    def start(self, platform: str, room_id: str, stream_url: str, streamer_name: str) -> bool:
        if self.is_recording:
            print(f"[Recorder] 已在录制中")
            return False

        self.platform = platform
        self.room_id = room_id
        self.streamer_name = streamer_name

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.output_dir / platform / room_id / timestamp / f"{streamer_name}_{timestamp}.flv"
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        success = False
        if self.tool == "streamlink":
            success = self._record_with_streamlink(stream_url)
        elif self.tool == "yt-dlp":
            success = self._record_with_ytdlp(stream_url)
        elif self.tool == "ffmpeg":
            success = self._record_with_ffmpeg(stream_url)
        else:
            print(f"[Recorder] 未找到可用的录制工具")

        if success:
            self.is_recording = True
            self.start_time = datetime.now()
        return success

    def _record_with_streamlink(self, stream_url: str) -> bool:
        cmd = [
            "streamlink",
            "--output", str(self.output_file),
            "--retry-max", "3",
            "--retry-open", "2",
            stream_url, "best"
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[Recorder] 使用 streamlink 开始录制: {self.output_file}")
            return True
        except Exception as e:
            print(f"[Recorder] streamlink 启动失败: {e}")
            return False

    def _record_with_ytdlp(self, stream_url: str) -> bool:
        cmd = [
            "yt-dlp",
            "-o", str(self.output_file),
            "--live-from-start",
            "--no-playlist",
            stream_url
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[Recorder] 使用 yt-dlp 开始录制: {self.output_file}")
            return True
        except Exception as e:
            print(f"[Recorder] yt-dlp 启动失败: {e}")
            return False

    def _record_with_ffmpeg(self, stream_url: str) -> bool:
        cmd = [
            "ffmpeg",
            "-i", stream_url,
            "-c", "copy",
            "-f", "flv",
            str(self.output_file)
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[Recorder] 使用 ffmpeg 开始录制: {self.output_file}")
            return True
        except Exception as e:
            print(f"[Recorder] ffmpeg 启动失败: {e}")
            return False

    def stop(self) -> bool:
        if not self.is_recording or not self.process:
            return False

        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            self.is_recording = False
            duration = 0
            if self.output_file.exists():
                file_size = self.output_file.stat().st_size
                if self.start_time:
                    duration = int((datetime.now() - self.start_time).total_seconds())
                print(f"[Recorder] 录制完成: {self.output_file.name}, 时长: {duration}秒, 大小: {file_size} bytes")
            else:
                print(f"[Recorder] 录制文件不存在")

            self.process = None
            return True

        except Exception as e:
            print(f"[Recorder] 停止录制失败: {e}")
            return False

    def get_status(self) -> dict:
        return {
            "is_recording": self.is_recording,
            "platform": self.platform,
            "room_id": self.room_id,
            "streamer_name": self.streamer_name,
            "output_file": str(self.output_file),
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "tool": self.tool,
            "running": self.process.poll() is None if self.process else False
        }


class RecorderManager:
    def __init__(self, output_dir: str = "recordings"):
        self.output_dir = output_dir
        self.recorders: dict = {}
        self.lock = threading.Lock()

    def start_recording(self, platform: str, room_id: str, stream_url: str, streamer_name: str) -> bool:
        key = f"{platform}:{room_id}"

        with self.lock:
            if key in self.recorders and self.recorders[key].is_recording:
                print(f"[RecorderManager] 已在录制: {key}")
                return True

            recorder = Recorder(self.output_dir)
            if recorder.start(platform, room_id, stream_url, streamer_name):
                self.recorders[key] = recorder
                return True
            return False

    def stop_recording(self, platform: str, room_id: str) -> bool:
        key = f"{platform}:{room_id}"

        with self.lock:
            if key in self.recorders:
                recorder = self.recorders[key]
                success = recorder.stop()
                if success:
                    del self.recorders[key]
                return success
            return False

    def stop_all(self):
        with self.lock:
            for recorder in self.recorders.values():
                recorder.stop()
            self.recorders.clear()

    def get_recorder_status(self, platform: str, room_id: str) -> Optional[dict]:
        key = f"{platform}:{room_id}"
        if key in self.recorders:
            return self.recorders[key].get_status()
        return None

    def get_all_recorders_status(self) -> list:
        with self.lock:
            return [r.get_status() for r in self.recorders.values()]


if __name__ == "__main__":
    recorder = Recorder()
    print(f"当前使用工具: {recorder.tool}")
    print(f"输出目录: {recorder.output_dir}")
