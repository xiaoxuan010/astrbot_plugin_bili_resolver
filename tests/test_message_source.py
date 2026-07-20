import asyncio
import inspect
import json
from types import SimpleNamespace

import pytest
from astrbot_plugin_bili_resolver import analysis_bilibili, main


class FakeEvent:
    def __init__(self, message_str, raw_message=None):
        self.message_str = message_str
        self.message_obj = SimpleNamespace(
            group_id=None,
            raw_message=raw_message,
            message=[],
        )
        self.stopped = False

    def stop_event(self):
        self.stopped = True

    def chain_result(self, chain):
        return chain

    def plain_result(self, text):
        return text


def make_plugin():
    plugin = object.__new__(main.BilibiliAnalysis)
    plugin.enable_auto_parse = True
    plugin.enable_search = True
    plugin.group_whitelist_mode = False
    plugin.group_list = []
    return plugin


async def collect_async_generator(generator):
    return [item async for item in generator]


def test_source_classifier_api_exists():
    assert hasattr(main, "_classify_message_source")


@pytest.mark.parametrize(
    ("text", "card_url", "expected"),
    [
        ("", "https://b23.tv/4Do4uFm", "card"),
        ("https://www.bilibili.com/video/BV1xx411c7mD", "", "url"),
        ("分享视频 https://b23.tv/sU8dEQS", "", "url"),
        ("BV1xx411c7mD", "", "bvid"),
        ("  BV1xx411c7mD  ", "", "bvid"),
        ("看看 BV1xx411c7mD", "", "text"),
        ("普通聊天消息", "", "text"),
        ("https://mybilibili.com/video/BV1xx411c7mD", "", "text"),
        ("https://notb23.tv/sU8dEQS", "", "text"),
    ],
)
def test_classifies_original_message_source(text, card_url, expected):
    assert main._classify_message_source(text, card_url) == expected


def test_classifies_realistic_onebot_bilibili_card():
    payload = {
        "app": "com.tencent.miniapp_01",
        "prompt": "[QQ小程序]测试视频",
        "meta": {
            "detail_1": {
                "title": "哔哩哔哩",
                "qqdocurl": "https://b23.tv/4Do4uFm?share_source=qq",
            }
        },
    }
    raw_message = [
        {
            "type": "json",
            "data": {"data": json.dumps(payload, ensure_ascii=False)},
        }
    ]

    card_url = main._extract_from_raw_message(raw_message)

    assert card_url == "https://b23.tv/4Do4uFm?share_source=qq"
    assert main._classify_message_source("", card_url) == "card"


def test_bili_keyword_accepts_source_parameter():
    signature = inspect.signature(analysis_bilibili.bili_keyword)
    assert "source" in signature.parameters
    assert signature.parameters["source"].default == "text"


def test_bili_keyword_passes_source_to_video_detail(monkeypatch):
    captured = {}

    async def fake_video_detail(url, session, **kwargs):
        captured.update(kwargs)
        return ["ok"], "https://www.bilibili.com/video/BV1xx411c7mD"

    monkeypatch.setattr(
        analysis_bilibili,
        "extract",
        lambda text: (
            "https://api.bilibili.com/x/web-interface/view?bvid=BV1xx411c7mD",
            None,
            None,
        ),
    )
    monkeypatch.setattr(analysis_bilibili, "video_detail", fake_video_detail)

    result = asyncio.run(
        analysis_bilibili.bili_keyword(
            None,
            "BV1xx411c7mD",
            session=object(),
            source="card",
        )
    )

    assert result == ["ok"]
    assert captured["source"] == "card"


@pytest.mark.parametrize(
    ("event", "expected_source", "expected_text"),
    [
        (
            FakeEvent(
                "",
                [
                    {
                        "type": "json",
                        "data": {
                            "data": json.dumps(
                                {
                                    "meta": {
                                        "detail_1": {
                                            "qqdocurl": "https://b23.tv/card123"
                                        }
                                    }
                                }
                            )
                        },
                    }
                ],
            ),
            "card",
            "https://www.bilibili.com/video/BV1xx411c7mD",
        ),
        (
            FakeEvent("分享 https://b23.tv/link123"),
            "url",
            "https://www.bilibili.com/video/BV1xx411c7mD",
        ),
        (
            FakeEvent("BV1xx411c7mD"),
            "bvid",
            "BV1xx411c7mD",
        ),
    ],
)
def test_on_message_propagates_original_source(
    monkeypatch,
    event,
    expected_source,
    expected_text,
):
    captured = {}

    async def fake_get_session(self):
        return object()

    async def fake_b23_extract(text, session):
        return "https://www.bilibili.com/video/BV1xx411c7mD"

    async def fake_bili_keyword(group_id, text, session, source="text"):
        captured.update(text=text, source=source)
        return ["ok"]

    monkeypatch.setattr(main.BilibiliAnalysis, "_get_session", fake_get_session)
    monkeypatch.setattr(main, "b23_extract", fake_b23_extract)
    monkeypatch.setattr(main, "bili_keyword", fake_bili_keyword)

    results = asyncio.run(
        collect_async_generator(make_plugin().on_message(event))
    )

    assert results
    assert event.stopped
    assert captured == {"text": expected_text, "source": expected_source}


def test_search_command_uses_text_source(monkeypatch):
    captured = {}
    event = FakeEvent("/搜视频 测试关键词")

    async def fake_get_session(self):
        return object()

    async def fake_search(keyword, session):
        captured["keyword"] = keyword
        return "https://www.bilibili.com/video/BV1xx411c7mD"

    async def fake_bili_keyword(group_id, text, session, source="text"):
        captured.update(text=text, source=source)
        return ["ok"]

    monkeypatch.setattr(main.BilibiliAnalysis, "_get_session", fake_get_session)
    monkeypatch.setattr(main, "search_bili_by_title", fake_search)
    monkeypatch.setattr(main, "bili_keyword", fake_bili_keyword)

    results = asyncio.run(
        collect_async_generator(make_plugin().search_video(event))
    )

    assert results
    assert event.stopped
    assert captured == {
        "keyword": "测试关键词",
        "text": "https://www.bilibili.com/video/BV1xx411c7mD",
        "source": "text",
    }
