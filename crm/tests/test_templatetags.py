from crm.templatetags.markdown_extras import markdown_filter


def test_renders_markdown():
    assert markdown_filter("Ett **viktigt** bolag.") == (
        "<p>Ett <strong>viktigt</strong> bolag.</p>"
    )


def test_empty_value_renders_empty_string():
    assert markdown_filter("") == ""
    assert markdown_filter(None) == ""


def test_escapes_raw_html():
    result = markdown_filter("<script>alert('xss')</script>")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_autolinks_bare_urls():
    result = markdown_filter("Se https://example.com/om-oss för mer info.")
    assert '<a href="https://example.com/om-oss">' in result


def test_autolink_preserves_query_string():
    result = markdown_filter("https://example.com/?a=1&b=2")
    assert '<a href="https://example.com/?a=1&amp;b=2">' in result


def test_explicit_markdown_links_still_work():
    result = markdown_filter("[hemsidan](https://example.com)")
    assert '<a href="https://example.com">hemsidan</a>' in result
