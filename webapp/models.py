"""Django models backing the webapp's positions, learning brain, and chat.

The filesystem memory tree remains the source of truth for the agent; these
tables are a synced, queryable projection (see memory_sync.py + learning.py).
"""
from django.conf import settings
from django.db import models


class ClientProfile(models.Model):
    """Per-client metadata. Tracks the one-time onboarding/disclaimer state."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    onboarded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user}: onboarded={self.onboarded_at}"


class Trade(models.Model):
    """A single trade/pick file (open, pending, watchlist, or closed)."""

    KIND_OPEN = "open"
    KIND_PENDING = "pending"
    KIND_WATCHLIST = "watchlist"
    KIND_CLOSED = "closed"
    KIND_CHOICES = [
        (KIND_OPEN, "Open"),
        (KIND_PENDING, "Pending"),
        (KIND_WATCHLIST, "Watchlist"),
        (KIND_CLOSED, "Closed"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trades"
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)
    file_name = models.CharField(max_length=120)
    ticker = models.CharField(max_length=16, db_index=True)
    date = models.CharField(max_length=32, blank=True, default="")
    direction = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=32, blank=True, default="")
    conviction = models.CharField(max_length=16, blank=True, default="")
    entry_price = models.CharField(max_length=32, blank=True, default="")
    entry_zone = models.CharField(max_length=64, blank=True, default="")
    stop_loss = models.CharField(max_length=32, blank=True, default="")
    exit_price = models.CharField(max_length=32, blank=True, default="")
    targets = models.CharField(max_length=256, blank=True, default="")
    horizon = models.CharField(max_length=32, blank=True, default="")
    risk_reward = models.TextField(blank=True, default="")
    outcome = models.CharField(max_length=64, blank=True, default="")
    note = models.TextField(blank=True, default="")
    rationale = models.TextField(blank=True, default="")
    signals_used = models.TextField(blank=True, default="")
    return_realized_pct = models.FloatField(null=True, blank=True)
    raw = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "kind", "file_name"], name="uniq_trade_per_user"
            )
        ]

    def __str__(self):
        return f"{self.ticker} ({self.kind})"


class Lesson(models.Model):
    """The shared learning brain (lessons.md), one row kept in sync."""

    content = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lesson #{self.pk}"


class SignalLog(models.Model):
    """Per-signal win-rate stats, shared across users (signals_log/*.md)."""

    name = models.CharField(max_length=64, unique=True)
    triggered_correctly = models.IntegerField(default=0)
    triggered_falsely = models.IntegerField(default=0)
    win_rate = models.FloatField(null=True, blank=True)
    # --- Expectancy-based evidence (added by the learning upgrade) ---------
    n_trades = models.IntegerField(default=0)
    n_missing_return = models.IntegerField(default=0)
    mean_return_pct = models.FloatField(null=True, blank=True)
    median_return_pct = models.FloatField(null=True, blank=True)
    total_return_pct = models.FloatField(null=True, blank=True)
    best_return_pct = models.FloatField(null=True, blank=True)
    worst_return_pct = models.FloatField(null=True, blank=True)
    verdict = models.CharField(max_length=16, blank=True, default="insufficient")
    evidence_note = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DailySignal(models.Model):
    """A clean, plain-English trading signal generated after a scan.

    Produced by a separate lightweight LLM call that reads the scan results
    and outputs simple buy/hold signals with entry, targets, stop, and reason.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_signals",
    )
    scan_date = models.DateField(db_index=True)
    ticker = models.CharField(max_length=16, db_index=True)
    direction = models.CharField(max_length=16, default="long")
    entry_low = models.FloatField(null=True, blank=True)
    entry_high = models.FloatField(null=True, blank=True)
    tp1 = models.FloatField(null=True, blank=True)
    tp2 = models.FloatField(null=True, blank=True)
    stop_loss = models.FloatField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scan_date", "ticker"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "scan_date", "ticker"], name="uniq_daily_signal"
            )
        ]

    def __str__(self):
        return f"{self.ticker} ({self.scan_date})"


class ScanRun(models.Model):
    """Tracks when a scan last ran for a user, and its mode."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scan_runs",
    )
    scan_date = models.DateField(db_index=True)
    mode = models.CharField(max_length=16, default="full")
    signal_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scan_date", "-created_at"]

    def __str__(self):
        return f"{self.owner}: {self.scan_date} ({self.mode})"


class ChatSession(models.Model):
    """A named chat conversation — groups messages and appears in the rail."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(max_length=128, blank=True, default="New chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.owner}: {self.title}"


class ChatMessage(models.Model):
    """Durable per-user chat history — belongs to a ChatSession."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=64, db_index=True)
    role = models.CharField(max_length=16)
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.owner} {self.role}: {self.content[:40]}"
