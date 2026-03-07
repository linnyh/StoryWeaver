from app.services.scene_image_service import _extract_image_url, _parse_prompt_list


def test_parse_prompt_list_supports_markdown_block():
    raw = '```json\n["镜头一", "镜头二"]\n```'
    prompts = _parse_prompt_list(raw)
    assert prompts == ["镜头一", "镜头二"]


def test_extract_image_url_supports_data_array():
    payload = {"data": [{"url": "https://example.com/a.png"}]}
    assert _extract_image_url(payload) == "https://example.com/a.png"


def test_extract_image_url_supports_output_object():
    payload = {"output": {"url": "https://example.com/b.png"}}
    assert _extract_image_url(payload) == "https://example.com/b.png"
