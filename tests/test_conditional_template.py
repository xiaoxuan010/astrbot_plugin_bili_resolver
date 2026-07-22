import asyncio

import pytest
from astrbot_plugin_bili_resolver import analysis_bilibili


def test_conditional_renderer_api_exists():
    assert hasattr(analysis_bilibili, "_render_conditionals")


SOURCE_TEMPLATE = (
    "prefix\n"
    "{% if source == \"miniapp\" %}\n"
    "miniapp\n"
    "{% elif source == \"card\" %}\n"
    "card\n"
    "{% elif source == \"url\" %}\n"
    "url\n"
    "{% elif source == \"bvid\" %}\n"
    "bvid\n"
    "{% else %}\n"
    "text\n"
    "{% endif %}\n"
    "suffix"
)


@pytest.mark.parametrize(
    ("source", "expected_branch"),
    [
        ("miniapp", "miniapp"),
        ("card", "card"),
        ("url", "url"),
        ("bvid", "bvid"),
        ("text", "text"),
    ],
)
def test_selects_source_branch(source, expected_branch):
    rendered = analysis_bilibili._render_conditionals(SOURCE_TEMPLATE, source)
    assert rendered == f"prefix\n{expected_branch}\nsuffix"


def test_preserves_legacy_template_exactly():
    template = "🎬 ${标题}\r\n${封面}\r\n🔗 ${链接}"
    assert analysis_bilibili._render_conditionals(template, "miniapp") == template


def test_renders_two_sequential_blocks():
    template = (
        "{% if source == \"url\" %}\nURL-A\n{% else %}\nOTHER-A\n{% endif %}\n"
        "{% if source == \"url\" %}\nURL-B\n{% endif %}\n"
    )
    assert analysis_bilibili._render_conditionals(template, "url") == (
        "URL-A\nURL-B\n"
    )


@pytest.mark.parametrize(
    ("template", "message"),
    [
        ("{% if source == \"unknown\" %}\nx\n{% endif %}\n", "未知来源"),
        ("{% elif source == \"url\" %}\nx\n", "缺少 if"),
        (
            "{% if source == \"url\" %}\nx\n"
            "{% else %}\ny\n{% else %}\nz\n{% endif %}\n",
            "重复 else",
        ),
        ("{% if source == \"url\" %}\nx\n", "缺少 endif"),
        (
            "{% if source == \"url\" %}\n"
            "{% if source == \"miniapp\" %}\nx\n"
            "{% endif %}\n{% endif %}\n",
            "嵌套",
        ),
        ("prefix {% if source == \"url\" %} suffix", "独占一行"),
        ("{% for item in items %}\nx\n", "不支持"),
    ],
)
def test_rejects_invalid_control_syntax(template, message):
    with pytest.raises(analysis_bilibili.TemplateSyntaxError, match=message):
        analysis_bilibili._render_conditionals(template, "url")


def test_rejects_unknown_runtime_source():
    with pytest.raises(analysis_bilibili.TemplateSyntaxError, match="未知消息来源"):
        analysis_bilibili._render_conditionals(SOURCE_TEMPLATE, "search")


def test_apply_template_skips_cover_in_unselected_branch():
    template = (
        "{% if source == \"miniapp\" %}\n"
        "${链接}\n"
        "{% else %}\n"
        "${封面}\n"
        "{% endif %}\n"
    )

    rendered = analysis_bilibili._apply_template(
        template,
        {"链接": "https://www.bilibili.com/video/av123"},
        "https://example.com/cover.jpg",
        source="miniapp",
    )

    assert rendered == ["https://www.bilibili.com/video/av123\n"]


def test_apply_template_emits_cover_in_selected_branch():
    template = (
        "{% if source == \"bvid\" %}\n"
        "封面：\n${封面}\n完成\n"
        "{% endif %}\n"
    )

    rendered = analysis_bilibili._apply_template(
        template,
        {},
        "https://example.com/cover.jpg",
        source="bvid",
    )

    assert rendered == [
        "封面：\n",
        "https://example.com/cover.jpg",
        "\n完成\n",
    ]


def test_apply_template_substitutes_variables_after_branch_selection():
    template = (
        "{% if source == \"url\" %}\n${BV号}\n{% else %}\n${链接}\n{% endif %}\n"
    )

    rendered = analysis_bilibili._apply_template(
        template,
        {"BV号": "BV1xx411c7mD", "链接": "https://example.com"},
        "",
        source="url",
    )

    assert rendered == ["BV1xx411c7mD\n"]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("miniapp", "🔗 https://www.bilibili.com/video/av123\n"),
        ("card", "🔗 https://www.bilibili.com/video/av123\n"),
        ("url", "BV1xx411c7mD\n"),
        ("bvid", "https://www.bilibili.com/video/av123\n"),
    ],
)
def test_recommended_template_matches_source_contract(source, expected):
    template = (
        "{% if source == \"miniapp\" %}\n"
        "🔗 ${链接}\n"
        "{% elif source == \"card\" %}\n"
        "🔗 ${链接}\n"
        "{% elif source == \"url\" %}\n"
        "${BV号}\n"
        "{% elif source == \"bvid\" %}\n"
        "${链接}\n"
        "{% else %}\n"
        "🎬 ${标题}\n👤 ${UP主}\n${封面}\n🔗 ${链接}\n"
        "{% endif %}\n"
    )
    data = {
        "标题": "测试视频",
        "UP主": "测试UP",
        "链接": "https://www.bilibili.com/video/av123",
        "BV号": "BV1xx411c7mD",
    }

    assert analysis_bilibili._apply_template(
        template,
        data,
        "https://example.com/cover.jpg",
        source=source,
    ) == [expected]


VIDEO_DATA = {
    "aid": 123,
    "bvid": "BV1xx411c7mD",
    "title": "测试视频",
    "pic": "https://example.com/cover.jpg",
    "pubdate": 0,
    "desc": "测试简介",
    "tname": "知识",
    "duration": 90,
    "copyright": 1,
    "pages": [],
    "owner": {"name": "测试UP", "mid": 456},
    "stat": {
        "like": 1,
        "coin": 2,
        "favorite": 3,
        "share": 4,
        "view": 5,
        "danmaku": 6,
        "reply": 7,
    },
}


class FakeResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def json(self):
        return {"data": VIDEO_DATA}


class FakeSession:
    def get(self, url):
        return FakeResponse()


def test_video_detail_passes_source_to_custom_template(monkeypatch):
    monkeypatch.setattr(analysis_bilibili, "analysis_display_image", False)
    monkeypatch.setattr(
        analysis_bilibili,
        "analysis_video_template",
        (
            "{% if source == \"url\" %}\n"
            "${BV号}\n"
            "{% else %}\n"
            "${链接}\n"
            "{% endif %}\n"
        ),
    )

    message, _ = asyncio.run(
        analysis_bilibili.video_detail(
            "https://api.bilibili.com/view",
            FakeSession(),
            source="url",
        )
    )

    assert message == ["BV1xx411c7mD\n"]


def test_video_detail_falls_back_on_template_syntax_error(monkeypatch):
    monkeypatch.setattr(analysis_bilibili, "analysis_display_image", False)
    monkeypatch.setattr(
        analysis_bilibili,
        "analysis_video_template",
        "{% if source == \"url\" %}\n${BV号}\n",
    )

    message, video_url = asyncio.run(
        analysis_bilibili.video_detail(
            "https://api.bilibili.com/view",
            FakeSession(),
            source="url",
        )
    )

    assert isinstance(message, list)
    assert any("标题：测试视频" in part for part in message)
    assert video_url == "https://www.bilibili.com/video/av123"
