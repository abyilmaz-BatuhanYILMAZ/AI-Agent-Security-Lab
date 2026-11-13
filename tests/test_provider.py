import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from agentsec_lab.models import CompatibleChatModel, ModelFailure


class LocalInferenceHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.seen.append((self.path, self.headers.get("Authorization")))
        size = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(size)
        if self.server.redirect:
            self.send_response(307)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/unexpected")
            self.end_headers()
            return
        body = json.dumps({
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "action": "answer",
                        "target": "",
                        "content": "local transport fixture",
                    })
                }
            }]
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class ProviderTransportTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), LocalInferenceHandler)
        self.server.redirect = False
        self.server.seen = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def client(self):
        return CompatibleChatModel(
            model="local-transport-fixture",
            endpoint=f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions",
            api_key_env="TEST_ONLY_API_KEY",
            timeout=5,
        )

    def test_local_model_adapter_decodes_structured_json(self):
        with patch.dict("os.environ", {"TEST_ONLY_API_KEY": "FAKE_TEST_KEY"}):
            decision = self.client().decide([{"role": "user", "content": "hello"}])
        self.assertEqual(decision.action, "answer")
        self.assertEqual(decision.content, "local transport fixture")
        self.assertEqual(self.server.seen[0][1], "Bearer FAKE_TEST_KEY")

    def test_adapter_refuses_redirect_instead_of_forwarding_key(self):
        self.server.redirect = True
        with patch.dict("os.environ", {"TEST_ONLY_API_KEY": "FAKE_TEST_KEY"}):
            with self.assertRaises(ModelFailure):
                self.client().decide([{"role": "user", "content": "hello"}])
        self.assertEqual(len(self.server.seen), 1)
        self.assertEqual(self.server.seen[0][0], "/v1/chat/completions")
