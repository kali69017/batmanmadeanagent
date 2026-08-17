"""Web views: token login, dashboard, SSE agent streams, positions."""
import json

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils.timezone import now
from rest_framework.authtoken.models import Token

from .agent_service import AgentRunner, reset_history
from .memory_sync import load_positions
from .models import ChatMessage, ChatSession
from .streaming import sse_response

import config

FASSET_SCAN_QUERY = (
    "Run a Fasset scan on the curated 44-ticker watchlist. "
    "Use run_screening with mode='fasset'. "
    "If you find good trade ideas, give me the top ones with entry zones, "
    "stop_losses, targets, and rationale. If no stocks are good to buy now, "
    "just suggest the best candidates as watchlist items with the condition "
    "that needs to be met before entry."
)

FULL_SCAN_QUERY = (
    "Run a full scan on the expanded 100+ ticker watchlist. "
    "Use run_screening with mode='full'. "
    "If you find good trade ideas, give me the top ones with entry zones, "
    "stop_losses, targets, and rationale. If no stocks are good to buy now, "
    "just suggest the best candidates as watchlist items with the condition "
    "that needs to be met before entry."
)

# Default: full scan
SCAN_QUERY = FULL_SCAN_QUERY


def _require_auth(view_func):
    """Decorator: return JSON 401 for unauthenticated API requests instead of
    an HTML redirect. Use on SSE/JSON endpoints that JS `fetch()` calls."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def is_onboarded(user) -> bool:
    """True once the user has acknowledged the one-time disclaimer."""
    from .models import ClientProfile
    profile, _ = ClientProfile.objects.get_or_create(user=user)
    return profile.onboarded_at is not None


def mark_onboarded(user) -> None:
    from django.utils import timezone
    from .models import ClientProfile
    profile, _ = ClientProfile.objects.get_or_create(user=user)
    profile.onboarded_at = timezone.now()
    profile.save(update_fields=["onboarded_at"])


def _ensure_session(request: HttpRequest) -> ChatSession:
    """Return a ChatSession for the current Django session.

    Creates one if it doesn't exist. Title can be updated later from the
    first user message.
    """
    if not request.session.session_key:
        request.session.save()
    sk = request.session.session_key
    sess, _ = ChatSession.objects.get_or_create(
        session_key=sk,
        defaults={"owner": request.user, "title": "New chat"},
    )
    return sess


def _session_to_dict(s: ChatSession) -> dict:
    return {
        "session_key": s.session_key,
        "title": s.title,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
        "message_count": s.messages.count(),
    }


def _generate_title(query: str) -> str:
    """Generate a short title from the first user message."""
    q = query.strip()
    # Remove common prefixes
    for prefix in ("what ", "how ", "tell me ", "show me ", "can you ", "please "):
        if q.lower().startswith(prefix):
            q = q[len(prefix):]
    return q[:60] + ("…" if len(q) > 60 else "")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        token_key = (request.POST.get("token") or "").strip()

        # Primary: email/password auth (for clients)
        if email and password:
            from django.contrib.auth import authenticate
            # Match by email OR username
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(email__iexact=email).first() or User.objects.filter(username__iexact=email).first()
            if user:
                authed = authenticate(request, username=user.username, password=password)
                if authed:
                    login(request, authed)
                    return redirect("onboarding" if not is_onboarded(authed) else "dashboard")
            error = "Email or password is incorrect."

        # Dev fallback: token paste
        elif token_key:
            token = Token.objects.select_related("user").filter(key=token_key).first()
            if token:
                login(request, token.user)
                return redirect("onboarding" if not is_onboarded(token.user) else "dashboard")
            error = "That token isn't valid."

        else:
            error = "Enter your email and password."

    return render(request, "webapp/login.html", {"error": error})


def logout_view(request: HttpRequest):
    if request.method == "POST":
        logout(request)
    return redirect("login")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@login_required
def dashboard(request: HttpRequest):
    if not is_onboarded(request.user):
        return redirect("onboarding")
    return render(request, "webapp/dashboard.html", {"user": request.user})


@login_required
def onboarding_view(request: HttpRequest):
    """One-time disclaimer/onboarding screen, shown on first login."""
    if is_onboarded(request.user):
        return redirect("dashboard")
    return render(request, "webapp/onboarding.html", {"user": request.user})


@login_required
def onboarding_complete(request: HttpRequest):
    """Mark the user as onboarded and send them to the dashboard."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    mark_onboarded(request.user)
    return redirect("dashboard")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@_require_auth
def positions_view(request: HttpRequest):
    return JsonResponse(load_positions(request.user.username))


@_require_auth
def today_signals_view(request: HttpRequest):
    """Return today's generated signals + the latest scan date."""
    from django.utils import timezone
    from .models import DailySignal, ScanRun

    today = timezone.localdate()
    signals_qs = DailySignal.objects.filter(owner=request.user, scan_date=today)

    latest_run = ScanRun.objects.filter(owner=request.user).first()

    signals = [{
        "ticker": s.ticker,
        "direction": s.direction,
        "entry_low": s.entry_low,
        "entry_high": s.entry_high,
        "tp1": s.tp1,
        "tp2": s.tp2,
        "stop_loss": s.stop_loss,
        "reason": s.reason,
    } for s in signals_qs]

    return JsonResponse({
        "scan_date": today.isoformat(),
        "latest_scan": latest_run.scan_date.isoformat() if latest_run else None,
        "latest_scan_mode": latest_run.mode if latest_run else None,
        "signals": signals,
    })


@_require_auth
def scan_stream(request: HttpRequest):
    # Scan is an internal/ops action — staff only.
    if not request.user.is_staff:
        return JsonResponse({"error": "Not authorized"}, status=403)
    mode = (request.GET.get("mode") or "full").strip()
    query = FASSET_SCAN_QUERY if mode == "fasset" else FULL_SCAN_QUERY
    runner = AgentRunner(username=request.user.username)
    return sse_response(runner.run(query, scan=True))


@_require_auth
def portfolio_summary_view(request: HttpRequest):
    """Aggregated portfolio data for the Portfolio screen.

    Returns active/waiting/closed positions plus win rate and average return
    computed from closed trades (the trust signals for a paying client).
    """
    from .models import Trade

    positions = load_positions(request.user.username)

    active = positions.get("open", [])
    waiting = positions.get("pending", [])
    closed = positions.get("closed", [])

    # Compute closed-trade stats
    returns = []
    wins = 0
    for c in closed:
        rp = c.get("return_realized_pct")
        if rp is not None:
            try:
                rp = float(rp)
                returns.append(rp)
                if rp >= 0:
                    wins += 1
            except (TypeError, ValueError):
                pass

    win_rate = round(wins / len(returns), 3) if returns else None
    avg_return = round(sum(returns) / len(returns), 2) if returns else None

    # Unrealized P&L for active positions
    total_pnl_pct = 0.0
    for a in active:
        pnl = a.get("pnl_pct")
        if pnl is not None:
            total_pnl_pct += float(pnl)

    def _active_dict(a):
        return {
            "ticker": a.get("ticker"),
            "entry_price": a.get("entry_price"),
            "live_price": a.get("live_price"),
            "pnl_pct": a.get("pnl_pct"),
            "stop_loss": a.get("stop_loss"),
            "date": a.get("date"),
            "conviction": a.get("conviction"),
        }

    def _waiting_dict(w):
        return {
            "ticker": w.get("ticker"),
            "entry_zone": w.get("entry_zone"),
            "entry_low": w.get("entry_low"),
            "entry_high": w.get("entry_high"),
            "stop_loss": w.get("stop_loss"),
            "date": w.get("date"),
            "reason": w.get("rationale") or w.get("note") or "",
        }

    def _closed_dict(c):
        return {
            "ticker": c.get("ticker"),
            "outcome": c.get("outcome"),
            "return_pct": c.get("return_realized_pct"),
            "date": c.get("date"),
            "direction": c.get("direction"),
        }

    return JsonResponse({
        "active": [_active_dict(a) for a in active],
        "waiting": [_waiting_dict(w) for w in waiting],
        "closed": [_closed_dict(c) for c in closed],
        "stats": {
            "open_count": len(active),
            "waiting_count": len(waiting),
            "closed_count": len(closed),
            "win_rate": win_rate,
            "avg_return": avg_return,
            "total_pnl_pct": round(total_pnl_pct, 2),
        },
    })


@_require_auth
def chat_stream(request: HttpRequest):
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"error": "Empty query"}, status=400)

    session = _ensure_session(request)

    # Auto-title from first message
    if session.title == "New chat":
        session.title = _generate_title(query)
        session.save(update_fields=["title"])

    runner = AgentRunner(
        username=request.user.username,
        session_key=session.session_key,
    )
    return sse_response(runner.run(query, scan=False))


# ── Chat sessions ─────────────────────────────────────────────────────────

@_require_auth
def chat_sessions_view(request: HttpRequest):
    """List all chat sessions for the current user."""
    sessions = ChatSession.objects.filter(
        owner=request.user,
        messages__isnull=False,
    ).annotate(
        msg_count=Count("messages"),
    ).filter(msg_count__gt=0).order_by("-updated_at")

    return JsonResponse({
        "sessions": [_session_to_dict(s) for s in sessions],
    })


@_require_auth
def chat_session_detail(request: HttpRequest, session_key: str):
    """Return messages for a specific chat session."""
    try:
        session = ChatSession.objects.get(
            owner=request.user, session_key=session_key,
        )
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    messages = session.messages.order_by("created_at").values("role", "content")
    return JsonResponse({
        "session": _session_to_dict(session),
        "messages": list(messages),
    })


@_require_auth
def chat_session_delete(request: HttpRequest, session_key: str):
    """Delete a chat session and its messages."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        session = ChatSession.objects.get(
            owner=request.user, session_key=session_key,
        )
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
    session.delete()
    return JsonResponse({"ok": True})


@_require_auth
def new_chat_session(request: HttpRequest):
    """Create a fresh chat session and return its key."""
    if not request.session.session_key:
        request.session.save()
    # Force a new Django session — this will give us a new session_key
    old_sk = request.session.session_key
    request.session.flush()
    if not request.session.session_key:
        request.session.save()
    new_sk = request.session.session_key
    ChatSession.objects.get_or_create(
        session_key=new_sk,
        defaults={"owner": request.user, "title": "New chat"},
    )
    return JsonResponse({"session_key": new_sk})


@_require_auth
def reset_chat_view(request: HttpRequest):
    """Reset the current chat session (clear messages, keep session)."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    session = _ensure_session(request)
    reset_history(request.user.username, session.session_key)
    return JsonResponse({"ok": True})


def health_view(request: HttpRequest):
    return JsonResponse({"ok": True})


@login_required
def admin_scan_view(request: HttpRequest):
    """Staff-only manual scan trigger screen (the old debug scan UI)."""
    if not request.user.is_staff:
        return redirect("dashboard")
    return render(request, "webapp/scan.html", {"user": request.user})
