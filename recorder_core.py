import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


class Recorder:
    def __init__(self, output_dir: str = "recordings", tool: str = ""):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process: Optional[subprocess.Popen] = None
        self.is_recording = False
        self.start_time: Optional[datetime] = None
        self.platform = ""
        self.room_id = ""
        self.streamer_name = ""
        self.output_file = ""
        self.tool = tool or self.detect_tool()

    @staticmethod
    def detect_tool() -> str:
        tools = ["streamlink", "yt-dlp", "ffmpeg"]
        for tool in tools:
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    return tool
            except Exception:
                continue
        return ""

    def start(self, platform: str, room_id: str, stream_url: str, streamer_name: str) -> bool:
        if self.is_recording:
            print("[Recorder] Already recording")
            return False

        self.platform = platform
        self.room_id = room_id
        self.streamer_name = streamer_name

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = streamer_name or f"{platform}_{room_id}"
        self.output_file = self.output_dir / platform / room_id / timestamp / f"{safe_name}_{timestamp}.flv"
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        if self.tool == "streamlink":
            success = self._record_with_streamlink(stream_url)
        elif self.tool == "yt-dlp":
            success = self._record_with_ytdlp(stream_url)
        elif self.tool == "ffmpeg":
            success = self._record_with_ffmpeg(stream_url)
        else:
            print("[Recorder] No recording tool detected")
            success = False

        if success:
            self.is_recording = True
            self.start_time = datetime.now()
        return success

    def _record_with_streamlink(self, stream_url: str) -> bool:
        cmd = [
            "streamlink",
            "--output",
            str(self.output_file),
            "--retry-max",
            "3",
            "--retry-open",
            "2",
            stream_url,
            "best",
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[Recorder] Started streamlink recording: {self.output_file}")
            return True
        except Exception as exc:
            print(f"[Recorder] streamlink start failed: {exc}")
            return False

    def _record_with_ytdlp(self, stream_url: str) -> bool:
        cmd = [
            "yt-dlp",
            "-o",
            str(self.output_file),
            "--live-from-start",
            "--no-playlist",
            stream_url,
        ]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[Recorder] Started yt-dlp recording: {self.output_file}")
            return True
        except Exception as exc:
            print(f"[Recorder] yt-dlp start failed: {exc}")
            return False

    def _record_with_ffmpeg(self, stream_url: str) -> bool:
        cmd = ["ffmpeg", "-i", stream_url, "-c", "copy", "-f", "flv", str(self.output_file)]
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[Recorder] Started ffmpeg recording: {self.output_file}")
            return True
        except Exception as exc:
            print(f"[Recorder] ffmpeg start failed: {exc}")
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
                print(
                    f"[Recorder] Recording finished: {self.output_file.name}, "
                    f"duration={duration}s, size={file_size} bytes"
                )
            else:
                print("[Recorder] Output file does not exist")

            self.process = None
            return True
        except Exception as exc:
            print(f"[Recorder] Stop recording failed: {exc}")
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
            "running": self.process.poll() is None if self.process else False,
        }


class RecorderManager:
    def __init__(self, output_dir: str = "recordings"):
        self.output_dir = output_dir
        self.recorders: dict = {}
        self.lock = threading.Lock()
        self.recording_tool = Recorder.detect_tool()
        print(f"[RecorderManager] Selected recording tool: {self.recording_tool or 'none'}")

    def start_recording(self, platform: str, room_id: str, stream_url: str, streamer_name: str) -> bool:
        key = f"{platform}:{room_id}"

        with self.lock:
            if key in self.recorders and self.recorders[key].is_recording:
                print(f"[RecorderManager] Already recording: {key}")
                return True

            recorder = Recorder(self.output_dir, tool=self.recording_tool)
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
    manager = RecorderManager()
    print(f"Current tool: {manager.recording_tool}")
