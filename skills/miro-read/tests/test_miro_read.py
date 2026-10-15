"""Synthetic public fixtures only. No account or board credentials are required."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "miro_read.py"


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.is_file():
            raise AssertionError("The portable Miro reader has not been implemented.")
        spec = importlib.util.spec_from_file_location("miro_read", SCRIPT)
        cls.reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.reader)

    def client(self, pages):
        client = self.reader.MiroClient("synthetic-test-credential")
        calls = []

        def get(path, params=None):
            calls.append((path, params or {}))
            return pages.pop(0)

        client.get = get
        return client, calls

    def test_board_url_and_percent_encoded_id(self):
        self.assertEqual(self.reader.board_id("https://miro.com/app/board/EXAMPLE_BOARD%3D/?moveToWidget=example-item"), "EXAMPLE_BOARD=")
        self.assertEqual(self.reader.board_id("EXAMPLE_BOARD="), "EXAMPLE_BOARD=")

    def test_untrusted_board_addresses_rejected(self):
        for value in ("https://example.invalid/app/board/TEST/", "http://miro.com/app/board/TEST/", "https://user@miro.com/app/board/TEST/", "https://miro.com:443/app/board/TEST/", "../../secrets", "https://miro.com/app/board/TEST/extra"):
            with self.subTest(value=value), self.assertRaises(self.reader.ReaderError):
                self.reader.board_id(value)

    def test_cursor_pagination_does_not_stop_at_first_page(self):
        client, calls = self.client([{"data":[{"id":"first"}], "cursor":"cursor+/="}, {"data":[{"id":"second"}]}])
        items = client.items("EXAMPLE_BOARD=")
        self.assertEqual([item["id"] for item in items], ["first", "second"])
        self.assertEqual(calls[1][1]["cursor"], "cursor+/=")

    def test_cursor_continues_across_empty_page(self):
        client, _ = self.client([{"data":[], "cursor":"next"}, {"data":[{"id":"last"}]}])
        self.assertEqual(len(client.items("TEST")), 1)

    def test_repeated_cursor_is_reported_instead_of_looping(self):
        client, _ = self.client([{"data":[], "cursor":"same"}, {"data":[], "cursor":"same"}])
        with self.assertRaises(self.reader.ReaderError): client.items("TEST")

    def test_page_limit_is_not_silent_partial_success(self):
        client, _ = self.client([{"data":[], "cursor":"next"}])
        with self.assertRaises(self.reader.ReaderError): client.items("TEST", max_pages=1)

    def test_boards_use_offset_not_item_cursor(self):
        client, calls = self.client([{"data":[{"id":"a"}], "total":2}, {"data":[{"id":"b"}], "total":2}])
        self.assertEqual(len(client.boards()), 2)
        self.assertEqual(calls[1][1]["offset"], 1)

    def test_connectors_use_their_own_endpoint(self):
        client, calls = self.client([{"data":[{"id":"edge", "startItem":{"id":"a"}, "endItem":{"id":"b"}}]}])
        self.assertEqual(len(client.items("TEST", collection="connectors")), 1)
        self.assertTrue(calls[0][0].endswith("/connectors"))

    def test_html_and_unicode_preserve_reading_order(self):
        self.assertEqual(self.reader.plain_text("<p>想法 &amp; 理由</p><ul><li>First</li><li>Second<br>line</li></ul>"), "想法 & 理由\n- First\n- Second\nline")

    def test_script_markup_is_not_presented_as_text(self):
        self.assertEqual(self.reader.plain_text("<script>hidden()</script><p>Read me</p>"), "Read me")

    def test_normalized_items_preserve_provenance_not_author_profiles(self):
        item = self.reader.normalize_item({"id":"note", "type":"sticky_note", "data":{"content":"<p>Note</p>"}, "parent":{"id":"frame"}, "modifiedAt":"2026-01-01T00:00:00Z", "createdBy":{"id":"synthetic-person"}}, "TEST")
        self.assertEqual(item["parent_id"], "frame")
        self.assertIn("moveToWidget=note", item["url"])
        self.assertNotIn("createdBy", item)
        self.assertEqual(item["text"], "Note")

    def test_unknown_item_is_retained_with_visual_gap(self):
        item = self.reader.normalize_item({"id":"drawing", "type":"unsupported"}, "TEST")
        self.assertTrue(item["needs_visual_review"])
        self.assertEqual(item["id"], "drawing")

    def test_frame_grouping_uses_parent_id(self):
        items = [self.reader.normalize_item({"id":"frame", "type":"frame", "data":{"title":"Workshop"}}, "TEST"), self.reader.normalize_item({"id":"child", "type":"text", "data":{"content":"Decision"}, "parent":{"id":"frame"}}, "TEST")]
        markdown = self.reader.render_markdown({"board":{"name":"Example", "url":"https://miro.com/app/board/TEST/"}, "retrieved_at":"2026-01-01T00:00:00Z", "items":items, "connectors":[], "coverage":{"connectors_fetched":False}, "warnings":[]})
        self.assertIn("Workshop", markdown)
        self.assertIn("Parent: frame", markdown)
        self.assertIn("Decision", markdown)
        self.assertIn("not fetched", markdown)

    def test_export_does_not_overwrite_previous_results(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "out"
            payload = {"board":{"name":"Example", "url":"https://miro.com/app/board/TEST/"}, "retrieved_at":"now", "items":[], "connectors":[], "coverage":{"connectors_fetched":False}, "warnings":[]}
            self.reader.write_export(payload, target)
            before = (target / "board.json").read_bytes()
            with self.assertRaises(self.reader.ReaderError): self.reader.write_export(payload, target)
            self.assertEqual((target / "board.json").read_bytes(), before)

    def test_missing_token_has_actionable_error(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(self.reader.ReaderError, "MIRO_ACCESS_TOKEN"):
            self.reader.client_from_env()

    def test_bearer_token_cannot_be_sent_to_foreign_host(self):
        with self.assertRaises(self.reader.ReaderError):
            self.reader.MiroClient("synthetic-test-credential").get("https://example.invalid/steal")

    def test_http_errors_do_not_echo_response_or_token(self):
        client = self.reader.MiroClient("synthetic-test-credential")
        error = HTTPError("https://api.miro.com/v2/boards", 401, "unauthorized", {}, io.BytesIO(b"private diagnostic content"))
        with patch.object(client.opener, "open", side_effect=error), self.assertRaises(self.reader.ReaderError) as raised:
            client.get("/boards")
        self.assertIn("401", str(raised.exception))
        self.assertNotIn("private", str(raised.exception))
        self.assertNotIn("synthetic-test-credential", str(raised.exception))

    def test_http_transport_sends_get_and_encodes_opaque_cursor(self):
        client = self.reader.MiroClient("synthetic-test-credential")
        response = io.BytesIO(b'{"data":[]}')
        with patch.object(client.opener, "open", return_value=response) as opened:
            client.get("/boards/TEST/items", {"cursor":"opaque+/="})
        request = opened.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(parse_qs(urlsplit(request.full_url).query)["cursor"], ["opaque+/="])

    def test_rate_limit_retries_are_bounded(self):
        client = self.reader.MiroClient("synthetic-test-credential")
        error = HTTPError("https://api.miro.com/v2/boards", 429, "rate limit", {"Retry-After":"0"}, None)
        with patch.object(client.opener, "open", side_effect=error) as opened, patch.object(self.reader.time, "sleep"):
            with self.assertRaises(self.reader.ReaderError): client.get("/boards")
        self.assertEqual(opened.call_count, 3)

    def test_two_step_image_reads_without_sending_bearer_to_storage(self):
        client, _ = self.client([{"id":"image", "type":"image", "data":{"imageUrl":"https://api.miro.com/v2/boards/TEST/resources/images/image"}}])
        requests = []

        def fetch(url, authenticated=True, accept="application/json", limit=None):
            requests.append((url, authenticated))
            if authenticated: return json.dumps({"url":"https://storage.example.invalid/picture.png"}).encode()
            return b"\x89PNG\r\n\x1a\nimage"

        client.fetch = fetch
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "picture.png"
            client.image("TEST", "image", output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG"))
        self.assertTrue(requests[0][1])
        self.assertFalse(requests[1][1])
        self.assertEqual(parse_qs(urlsplit(requests[0][0]).query)["format"], ["original"])

    def test_image_resource_cannot_redirect_auth_to_other_board(self):
        client, _ = self.client([{"type":"image", "data":{"imageUrl":"https://api.miro.com/v2/boards/OTHER/resources/images/image"}}])
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(self.reader.ReaderError):
            client.image("TEST", "image", Path(folder) / "image.png")

    def test_current_api_image_resource_path_is_supported(self):
        client, _ = self.client([{"type":"image", "data":{"imageUrl":"https://api.miro.com/v2/boards/TEST/resources/EXAMPLE_RESOURCE?format=preview"}}])
        client.fetch = lambda *args, **kwargs: b"\x89PNG\r\n\x1a\nimage"
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "image.png"
            client.image("TEST", "image", output)
            self.assertTrue(output.is_file())

    def test_image_resource_path_traversal_is_rejected_before_network(self):
        client, _ = self.client([{"type":"image", "data":{"imageUrl":"https://api.miro.com/v2/boards/TEST/resources/images/../../OTHER"}}])
        with patch.object(client, "fetch", return_value=b"\x89PNG\r\n\x1a\nimage") as fetched, tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(self.reader.ReaderError): client.image("TEST", "image", Path(folder) / "image.png")
            fetched.assert_not_called()

    def test_html_resource_is_not_saved_as_image(self):
        client, _ = self.client([{"type":"image", "data":{"imageUrl":"https://api.miro.com/v2/boards/TEST/resources/images/image"}}])
        client.fetch = lambda *args, **kwargs: b"\n<HTML><body>not an image</body></HTML>"
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "image.png"
            with self.assertRaises(self.reader.ReaderError): client.image("TEST", "image", output)
            self.assertFalse(output.exists())

    def test_authenticated_redirect_is_refused(self):
        handler = self.reader.NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "redirect", {}, "https://example.invalid/"))


if __name__ == "__main__":
    unittest.main()
