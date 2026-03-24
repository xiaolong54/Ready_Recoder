import subprocess
import time
import os
from pathlib import Path
from datetime import datetime
from config import RECORDINGS_DIR
from metadata import MetadataManager


class LiveRecorder:
    def __init__(self):
        self.metadata = MetadataManager()
        self.process = None

    def _check_tool(self, tool):
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            return True
        except:
            return False

    def get_available_tools(self):
        return {
            "streamlink": self._check_tool("streamlink"),
            "yt-dlp": self._check_tool("yt-dlp"),
            "ffmpeg": self._check_tool("ffmpeg"),
        }

    def record(self, room_url, streamer_name, duration=None):
        tools = self.get_available_tools()
        print(f"[Recorder] 可用工具: {tools}")

        if tools["streamlink"]:
            return self._record_with_streamlink(room_url, streamer_name, duration)
        elif tools["yt-dlp"]:
            return self._record_with_ytdlp(room_url, streamer_name, duration)
        elif tools["ffmpeg"]:
            return self._record_with_ffmpeg(room_url, streamer_name, duration)
        else:
            print("[Recorder] 错误: 没有可用的录制工具")
            return False

    def _record_with_streamlink(self, room_url, streamer_name, duration):
        filename = f"{streamer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = RECORDINGS_DIR / filename
        start_time = datetime.now()

        cmd = [
            "streamlink",
            "--output", str(filepath),
            "--timeout", "10",
            "--retry-max", "3",
            room_url, "best"
        ]

        print(f"[Recorder] 使用streamlink开始录制: {room_url}")
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)

            if self.process.poll() is not None:
                print("[Recorder] streamlink启动失败")
                return False

            return self._monitor_recording(filepath, streamer_name, start_time, duration, "streamlink")
        except Exception as e:
            print(f"[Recorder] streamlink异常: {e}")
            return False

    def _record_with_ytdlp(self, room_url, streamer_name, duration):
        filename = f"{streamer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.%(ext)s"
        filepath = RECORDINGS_DIR / filename
        start_time = datetime.now()

        cmd = ["yt-dlp", "-o", str(filepath), "--live-from-start", room_url]

        print(f"[Recorder] 使用yt-dlp开始录制: {room_url}")
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)

            if self.process.poll() is not None:
                print("[Recorder] yt-dlp启动失败")
                return False

            return self._monitor_recording(filepath, streamer_name, start_time, duration, "yt-dlp")
        except Exception as e:
            print(f"[Recorder] yt-dlp异常: {e}")
            return False

    def _record_with_ffmpeg(self, room_url, streamer_name, duration):
        filename = f"{streamer_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = RECORDINGS_DIR / filename
        start_time = datetime.now()

        cmd = ["ffmpeg", "-i", room_url, "-c", "copy"]
        if duration:
            cmd.extend(["-t", str(duration)])
        cmd.append(str(filepath))

        print(f"[Recorder] 使用ffmpeg开始录制: {room_url}")
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return self._monitor_recording(filepath, streamer_name, start_time, duration, "ffmpeg")
        except Exception as e:
            print(f"[Recorder] ffmpeg异常: {e}")
            return False

    def _monitor_recording(self, filepath, streamer_name, start_time, duration, tool):
        elapsed = 0
        while True:
            if self.process and self.process.poll() is not None:
                print("[Recorder] 录制进程已结束")
                break
            if duration and elapsed >= duration:
                print(f"[Recorder] 达到指定时长 {duration}秒，停止录制")
                self.stop()
                break
            time.sleep(1)
            elapsed += 1
            if elapsed % 30 == 0:
                print(f"[Recorder] 已录制 {elapsed} 秒...")

        end_time = datetime.now()
        actual_duration = (end_time - start_time).seconds

        target_file = None
        if tool == "yt-dlp":
            for f in RECORDINGS_DIR.glob(f"{streamer_name}_*"):
                if f.is_file() and f.stat().st_size > 0:
                    target_file = f
                    break
        else:
            if filepath.exists():
                target_file = filepath

        if target_file:
            file_size = target_file.stat().st_size
            self.metadata.add_recording({
                "type": "live_record",
                "filename": target_file.name,
                "streamer_name": streamer_name,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": actual_duration,
                "file_size": file_size,
                "source_url": "",
                "tool": tool,
            })
            print(f"[Recorder] 录制完成: {target_file.name}, 时长: {actual_duration}秒")
            return True

        print("[Recorder] 未找到录制文件")
        return False

    def stop(self):
        if self.process and self.process.poll() is None:
            print("[Recorder] 停止录制...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()


if __name__ == "__main__":
    recorder = LiveRecorder()
    tools = recorder.get_available_tools()
    print(f"可用录制工具: {tools}")
