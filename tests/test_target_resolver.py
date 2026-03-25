from target_resolver import TargetResolver


class FakeDouyinClient:
    def __init__(self, users=None):
        self.users = users or []

    def search_user(self, keyword, limit=20):
        return self.users[:limit]


def test_search_targets_supports_url(monkeypatch):
    resolver = TargetResolver(FakeDouyinClient())
    monkeypatch.setattr(
        "target_resolver.PlatformParser.parse_url",
        lambda query: {"platform": "douyin", "room_id": "8888"},
    )

    result = resolver.search_targets("douyin", "https://live.douyin.com/8888")
    assert len(result) == 1
    assert result[0]["source"] == "url"
    assert result[0]["room_id"] == "8888"


def test_search_targets_supports_id_input():
    resolver = TargetResolver(FakeDouyinClient())
    result = resolver.search_targets("douyin", "123456")
    assert result == [
        {
            "platform": "douyin",
            "room_id": "123456",
            "nickname": "",
            "uid": "123456",
            "source": "id",
        }
    ]


def test_search_targets_supports_name_input_for_douyin(monkeypatch):
    resolver = TargetResolver(
        FakeDouyinClient(
            users=[
                {"uid": "111", "nickname": "A"},
                {"uid": "222", "nickname": "B"},
            ]
        )
    )
    monkeypatch.setattr("target_resolver.PlatformParser.parse_url", lambda query: None)

    result = resolver.search_targets("douyin", "主播名", limit=10)
    assert [item["room_id"] for item in result] == ["111", "222"]
    assert all(item["source"] == "name" for item in result)
