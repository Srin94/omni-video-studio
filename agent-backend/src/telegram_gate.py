"""Telegram Human-in-the-Loop approval gate (spec: Telegram Gate).

Sends the rendered video + title + summary + pinned comment to the operator with
[Approve & Upload] / [Cancel] inline buttons, then polls getUpdates for a
callback.

FAIL-CLOSED: if no explicit "Approve" arrives within APPROVAL_WINDOW_MINUTES, the
video is NOT published. Set APPROVE_ON_TIMEOUT=true to auto-publish on timeout.

If Telegram is not configured, `request_approval` returns approved=True so local
hands-on runs without a bot still proceed.
"""

from __future__ import annotations

import html
import time
from dataclasses import dataclass

import httpx

try:
    from . import config
    from .schema import OmniRenderPayload
except ImportError:  # pragma: no cover
    import config  # type: ignore
    from schema import OmniRenderPayload  # type: ignore

_API = "https://api.telegram.org/bot{token}/{method}"
APPROVE = "omni_approve"
REJECT = "omni_reject"
_TG_MAX_UPLOAD = 49 * 1024 * 1024  # Telegram caps uploads at 50MB


@dataclass
class ApprovalResult:
    approved: bool
    reason: str


def _call(method: str, **params):
    url = _API.format(token=config.TELEGRAM_BOT_TOKEN, method=method)
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, data=params)
        resp.raise_for_status()
        return resp.json()


def notify(text: str) -> None:
    if not config.has_telegram():
        return
    try:
        _call("sendMessage", chat_id=config.TELEGRAM_CHAT_ID, text=text)
    except Exception as exc:  # noqa: BLE001
        print(f"[telegram] notify failed ({exc}).")


def _caption(payload: OmniRenderPayload) -> str:
    thumb_ok = config.THUMBNAIL_PATH.exists() and config.THUMBNAIL_PATH.stat().st_size > 0
    thumb_line = (
        "\U0001F5BC️ Thumbnail: generated"
        if thumb_ok
        else "⚠️ Thumbnail: NOT generated — YouTube would use an auto-frame"
    )
    return (
        f"\U0001F3AC <b>{html.escape(payload.youtube_title)}</b>\n\n"
        f"Genre: <code>{html.escape(payload.genre)}</code>  |  "
        f"Format: <code>{html.escape(payload.video_format)}</code>\n"
        f"Duration: <code>{payload.total_duration_sec:.0f}s</code>  |  "
        f"Scenes: <code>{len(payload.scenes)}</code>  |  "
        f"BGM: <code>{html.escape(payload.suggested_bgm_mood)}</code>\n"
        f"{thumb_line}\n\n"
        f"<b>Pinned comment:</b>\n{html.escape(payload.pinned_comment[:400])}"
    )[:1024]


def _send_preview(payload: OmniRenderPayload) -> None:
    import json as _json

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve & Upload", "callback_data": APPROVE},
            {"text": "❌ Cancel", "callback_data": REJECT},
        ]]
    }
    data = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "caption": _caption(payload),
        "parse_mode": "HTML",
        "reply_markup": _json.dumps(keyboard),
    }
    video_ok = config.FINAL_VIDEO_PATH.exists() and config.FINAL_VIDEO_PATH.stat().st_size <= _TG_MAX_UPLOAD

    with httpx.Client(timeout=180.0) as client:
        if video_ok:
            url = _API.format(token=config.TELEGRAM_BOT_TOKEN, method="sendVideo")
            files = {"video": ("final_video.mp4", open(config.FINAL_VIDEO_PATH, "rb"), "video/mp4")}
            if config.THUMBNAIL_PATH.exists():
                files["thumbnail"] = ("thumbnail.png", open(config.THUMBNAIL_PATH, "rb"), "image/png")
            data["supports_streaming"] = "true"
            try:
                resp = client.post(url, data=data, files=files)
                resp.raise_for_status()
                return
            except Exception as exc:  # noqa: BLE001
                print(f"[telegram] sendVideo failed ({exc}); falling back to thumbnail.")
            finally:
                for f in files.values():
                    f[1].close()

        if config.THUMBNAIL_PATH.exists():
            url = _API.format(token=config.TELEGRAM_BOT_TOKEN, method="sendPhoto")
            with open(config.THUMBNAIL_PATH, "rb") as img:
                resp = client.post(url, data=data, files={"photo": ("thumbnail.png", img, "image/png")})
                resp.raise_for_status()
        else:
            # No media at all — send the caption as plain text with the buttons.
            data2 = {k: v for k, v in data.items() if k != "caption"}
            data2["text"] = _caption(payload)
            _call("sendMessage", **data2)


def _poll_for_decision(deadline: float) -> ApprovalResult:
    offset = None
    while time.time() < deadline:
        try:
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset
            data = _call("getUpdates", **params)
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                cb = update.get("callback_query")
                if not cb:
                    continue
                decision = cb.get("data")
                try:
                    _call("answerCallbackQuery", callback_query_id=cb["id"])
                except Exception:  # noqa: BLE001
                    pass
                if decision == APPROVE:
                    return ApprovalResult(True, "operator approved")
                if decision == REJECT:
                    return ApprovalResult(False, "operator rejected")
        except Exception as exc:  # noqa: BLE001
            print(f"[telegram] poll error ({exc}); retrying.")
            time.sleep(3)
    if config.APPROVE_ON_TIMEOUT:
        return ApprovalResult(True, "auto-approved on timeout (APPROVE_ON_TIMEOUT)")
    return ApprovalResult(False, "no response within window; not publishing (fail-closed)")


def request_approval(payload: OmniRenderPayload) -> ApprovalResult:
    if not config.has_telegram():
        print("[telegram] Not configured; auto-approving (no HITL gate).")
        return ApprovalResult(True, "telegram not configured; auto-approved")

    try:
        _send_preview(payload)
    except Exception as exc:  # noqa: BLE001
        approved = config.APPROVE_ON_TIMEOUT
        print(f"[telegram] Failed to send preview ({exc}); "
              f"{'auto-approving' if approved else 'NOT publishing (fail-closed)'}.")
        return ApprovalResult(approved, f"preview send failed: {exc}")

    minutes = config.APPROVAL_WINDOW_MINUTES
    print(f"[telegram] Preview sent. Waiting up to {minutes} min for a decision...")
    result = _poll_for_decision(time.time() + minutes * 60)
    print(f"[telegram] Decision: approved={result.approved} ({result.reason})")

    try:
        if result.approved:
            msg = "✅ Publishing now."
        elif "rejected" in result.reason:
            msg = "\U0001F6D1 Upload cancelled."
        else:
            msg = f"⌛ No response in {minutes} min — NOT published (fail-closed)."
        _call("sendMessage", chat_id=config.TELEGRAM_CHAT_ID, text=msg)
    except Exception:  # noqa: BLE001
        pass
    return result
