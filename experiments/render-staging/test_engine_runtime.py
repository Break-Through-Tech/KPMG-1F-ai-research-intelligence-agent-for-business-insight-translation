from concurrent.futures import ThreadPoolExecutor
import unittest

from engine_runtime import SESSION, engine_settings, session_token


class EngineRuntimeTests(unittest.TestCase):
    def test_defaults_and_experimental_opt_in(self):
        self.assertEqual(engine_settings({}), ('baseline', False))
        self.assertEqual(engine_settings({'RESEARCH_ENGINE': 's2'}), ('s2', False))
        self.assertEqual(engine_settings({'RESEARCH_ENGINE': 's2', 'S2_PAPER_BALANCE': '1'}), ('s2', True))
        for invalid in ({'RESEARCH_ENGINE': 'other'}, {'S2_PAPER_BALANCE': '1'},
                        {'RESEARCH_ENGINE': 's2', 'S2_PAPER_BALANCE': 'true'}):
            with self.assertRaises(ValueError):
                engine_settings(invalid)

    def test_cookie_recovery_and_signature_rejection(self):
        identity, cookie = session_token(None, b'fixture')
        header = cookie.split(';', 1)[0]
        self.assertEqual(session_token(header, b'fixture'), (identity, None))
        self.assertNotEqual(session_token(header, b'other')[0], identity)
        self.assertNotEqual(session_token(header + 'x', b'fixture')[0], identity)

    def test_concurrent_request_contexts_do_not_share_sessions(self):
        from threading import Barrier
        barrier = Barrier(2)

        def request():
            identity, _ = session_token(None, b'fixture')
            token = SESSION.set(identity)
            try:
                barrier.wait(timeout=5)
                self.assertEqual(SESSION.get(), identity)
                return identity
            finally:
                SESSION.reset(token)

        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = (executor.submit(request) for _ in range(2))
            self.assertNotEqual(first.result(), second.result())
        self.assertIsNone(SESSION.get())
