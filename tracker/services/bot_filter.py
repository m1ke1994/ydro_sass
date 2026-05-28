from dataclasses import dataclass, field


_BOT_UA_SUBSTRINGS = (
    "googlebot",
    "applebot",
    "bingbot",
    "headless",
    "curl",
    "python-requests",
    "wget",
)


@dataclass
class BotCheckResult:
    is_bot: bool = False
    reasons: list[str] = field(default_factory=list)
    request_count_5s: int | None = None
    unique_urls_10s: int | None = None

    def add_reason(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)
            self.is_bot = True


def detect_bot_visit(*, site_id: int, ip_address: str | None, user_agent: str | None, tracked_url: str | None = None) -> BotCheckResult:
    # UA-only bot detection (temporary simplification): no path/rate/IP heuristics.
    _ = site_id, ip_address, tracked_url
    result = BotCheckResult()
    ua = (user_agent or "").strip()

    if not ua:
        result.add_reason("empty_user_agent")
        return result

    ua_lower = ua.lower()
    for token in _BOT_UA_SUBSTRINGS:
        if token in ua_lower:
            result.add_reason(f"user_agent:{token}")

    return result
