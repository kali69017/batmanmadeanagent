"""Django tests for the signal-learning upgrade.

Runs under `manage.py test webapp`. Each test points config.USERS_ROOT and
config.SHARED_MEMORY_ROOT at fresh temp dirs so tests NEVER touch the real
`agent_fs` live data, then exercises the full closed-trade -> signals_log
markdown -> SignalLog DB pipeline via webapp.learning.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from django.test import TestCase

import config
from webapp import learning
from webapp.models import SignalLog


class SignalLearningTest(TestCase):
    def setUp(self):
        # Isolate the learning system from real agent_fs by redirecting roots
        # to a temp dir under the project (inside the writable workspace).
        base = Path(__file__).resolve().parent.parent / "webapp" / ".test_tmp"
        base.mkdir(parents=True, exist_ok=True)
        self._tmp = base
        self._users_root = self._tmp / "users"
        self._shared_root = self._tmp / "memories"
        (self._shared_root / "signals_log").mkdir(parents=True, exist_ok=True)
        self._orig_users = config.USERS_ROOT
        self._orig_shared = config.SHARED_MEMORY_ROOT
        config.USERS_ROOT = self._users_root
        config.SHARED_MEMORY_ROOT = self._shared_root
        SignalLog.objects.all().delete()

    def tearDown(self):
        config.USERS_ROOT = self._orig_users
        config.SHARED_MEMORY_ROOT = self._orig_shared
        SignalLog.objects.all().delete()
        for p in (self._users_root, self._shared_root):
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)

    def _make_closed_trade(self, name, ticker, date, signals, return_pct,
                           user_root="testuser"):
        root = config.USERS_ROOT / user_root / "memories" / "closed_trades"
        root.mkdir(parents=True, exist_ok=True)
        fp = root / f"{date}--{ticker}.md"
        body = (
            "---\n"
            f"date: {date}\n"
            f"ticker: {ticker}\n"
            f"status: closed\n"
            f"direction: long\n"
            f"signals_used: [{signals}]\n"
            f"return_realized_pct: {return_pct}\n"
            "---\n"
        )
        fp.write_text(body, encoding="utf-8")
        return fp

    def test_empty_signals_log_ok(self):
        learning.reinforce_learning()  # must not raise

    def test_single_signal_insufficient_sample(self):
        self._make_closed_trade("siga", "XOM", "2026-01-01", "siga", 1.0)
        summary = learning.reinforce_learning()
        self.assertIn("siga", summary)
        self.assertEqual(summary["siga"]["n_trades"], 1)
        self.assertEqual(summary["siga"]["verdict"], "insufficient")
        row = SignalLog.objects.get(name="siga")
        self.assertEqual(row.n_trades, 1)
        self.assertEqual(row.verdict, "insufficient")
        self.assertAlmostEqual(row.mean_return_pct, 1.0)

    def test_confirmed_signal_persists(self):
        for i in range(12):
            self._make_closed_trade("sigb", "CVX", f"2026-01-{i+1:02d}", "sigb", 1.0)
        summary = learning.reinforce_learning()
        self.assertEqual(summary["sigb"]["n_trades"], 12)
        self.assertEqual(summary["sigb"]["verdict"], "confirmed")
        row = SignalLog.objects.get(name="sigb")
        self.assertEqual(row.verdict, "confirmed")
        self.assertAlmostEqual(row.mean_return_pct, 1.0)

    def test_negative_expectancy_failing(self):
        for i in range(12):
            self._make_closed_trade("sigc", "META", f"2026-02-{i+1:02d}", "sigc", -1.0)
        summary = learning.reinforce_learning()
        self.assertEqual(summary["sigc"]["verdict"], "failing")
        self.assertEqual(SignalLog.objects.get(name="sigc").verdict, "failing")

    def test_high_win_rate_low_expectancy_not_confirmed(self):
        # 12 small wins (+0.2) + 8 big losses (-3) => 60% win but negative
        # expectancy => must be "failing", never "confirmed".
        for i in range(12):
            self._make_closed_trade("sigd", "AAPL", f"2026-03-{i+1:02d}", "sigd", 0.2)
        for i in range(8):
            self._make_closed_trade("sigd", "AAPL", f"2026-04-{i+1:02d}", "sigd", -3.0)
        summary = learning.reinforce_learning()
        s = summary["sigd"]
        self.assertGreater(s["win_rate"], 0.5)
        self.assertLess(s["mean_return_pct"], 0)
        self.assertEqual(s["verdict"], "failing")

    def test_markdown_file_has_evidence_fields(self):
        for i in range(12):
            self._make_closed_trade("sige", "MSFT", f"2026-05-{i+1:02d}", "sige", 0.5)
        learning.reinforce_learning()
        fp = config.SHARED_MEMORY_ROOT / "signals_log" / "sige.md"
        self.assertTrue(fp.exists())
        text = fp.read_text(encoding="utf-8")
        for field in ("n_trades:", "mean_return_pct:", "verdict:",
                      "evidence_note:", "median_return_pct:"):
            self.assertIn(field, text)

