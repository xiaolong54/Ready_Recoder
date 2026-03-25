from recorder_core import Recorder, RecorderManager


def test_recording_tool_detected_once(monkeypatch):
    counter = {"calls": 0}

    def fake_detect_tool():
        counter["calls"] += 1
        return "ffmpeg"

    monkeypatch.setattr(Recorder, "detect_tool", staticmethod(fake_detect_tool))

    def fake_start(self, platform, room_id, stream_url, streamer_name):
        self.is_recording = True
        return True

    monkeypatch.setattr(Recorder, "start", fake_start)

    manager = RecorderManager(output_dir="recordings")
    assert manager.recording_tool == "ffmpeg"

    assert manager.start_recording("douyin", "1", "url1", "a") is True
    assert manager.start_recording("douyin", "2", "url2", "b") is True

    assert counter["calls"] == 1
