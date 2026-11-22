from io import BufferedReader, BytesIO

from intiligence_mcp.server import _strip_initial_utf8_bom


def test_strips_utf8_bom_from_first_stdio_frame():
    payload = b'{"jsonrpc":"2.0","id":1}\n'
    stream = BufferedReader(BytesIO(b"\xef\xbb\xbf" + payload))

    _strip_initial_utf8_bom(stream)

    assert stream.readline() == payload


def test_leaves_bom_free_stdio_frame_unchanged():
    payload = b'{"jsonrpc":"2.0","id":1}\n'
    stream = BufferedReader(BytesIO(payload))

    _strip_initial_utf8_bom(stream)

    assert stream.readline() == payload
