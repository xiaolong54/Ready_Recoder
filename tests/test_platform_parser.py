from platform_parser import DouyuParser


class MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_douyu_get_live_status_calls_requests_with_url(monkeypatch):
    parser = DouyuParser()
    called = {}

    def fake_get(url, **kwargs):
        called["url"] = url
        called["kwargs"] = kwargs
        return MockResponse(
            {
                "error": 0,
                "data": {
                    "room_status": "1",
                    "room_id": "2001",
                    "room_name": "title",
                    "nickname": "anchor",
                    "room_thumb": "cover",
                },
            }
        )

    monkeypatch.setattr("platform_parser.requests.get", fake_get)

    status = parser.get_live_status("douyu", "2001")
    assert called["url"] == "https://open.douyucdn.cn/api/RoomApi/room/2001"
    assert called["kwargs"].get("timeout") == 10
    assert status["is_live"] is True


def test_douyu_get_live_status_returns_none_on_invalid_json(monkeypatch):
    parser = DouyuParser()

    class BadResponse:
        def json(self):
            raise ValueError("bad json")

    monkeypatch.setattr("platform_parser.requests.get", lambda *args, **kwargs: BadResponse())

    assert parser.get_live_status("douyu", "2002") is None
