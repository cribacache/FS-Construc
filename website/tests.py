from django.test import RequestFactory, SimpleTestCase, override_settings

from .ratelimit import get_client_ip


class ClientIpTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, forwarded=None):
        extra = {"REMOTE_ADDR": "10.0.0.1"}
        if forwarded:
            extra["HTTP_X_FORWARDED_FOR"] = forwarded
        return self.factory.get("/", **extra)

    @override_settings(TRUSTED_PROXY_HOPS=0)
    def test_legacy_mode_uses_first_entry(self):
        self.assertEqual(get_client_ip(self.request("1.1.1.1, 2.2.2.2")), "1.1.1.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_one_hop_uses_last_entry_so_spoofed_header_is_ignored(self):
        # nginx sets X-Forwarded-For to the real peer; anything a client
        # sent ahead of it must not be trusted.
        self.assertEqual(get_client_ip(self.request("6.6.6.6, 9.9.9.9")), "9.9.9.9")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_two_hops_uses_second_from_right(self):
        self.assertEqual(get_client_ip(self.request("6.6.6.6, 9.9.9.9, 3.3.3.3")), "9.9.9.9")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_fewer_entries_than_hops_falls_back_to_remote_addr(self):
        self.assertEqual(get_client_ip(self.request("9.9.9.9")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_no_header_falls_back_to_remote_addr(self):
        self.assertEqual(get_client_ip(self.request()), "10.0.0.1")
