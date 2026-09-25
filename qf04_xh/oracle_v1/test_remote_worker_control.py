import unittest

from remote_worker_control import _parse_remote_port


class RelayOutputParsingTests(unittest.TestCase):
    def test_accepts_current_bore_remote_port_log_format(self):
        line = (
            "2026-08-29T05:48:16.963530Z  INFO bore_cli::client: "
            "connected to server remote_port=5041"
        )

        self.assertEqual(_parse_remote_port(line), 5041)

    def test_preserves_legacy_bore_host_port_log_format(self):
        self.assertEqual(_parse_remote_port("listening at bore.pub:25117"), 25117)


if __name__ == "__main__":
    unittest.main()
