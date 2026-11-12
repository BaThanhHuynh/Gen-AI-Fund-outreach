import sqlite3
from typing import Any
from outreach.db import kv_set, record_usage


class FakeXClient:
    """Mock X client for local testing and offline execution with zero network access."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.sent: list[tuple[str, str]] = []
        self.inbox: list[dict[str, Any]] = []
        self.fail_next: Exception | None = None

        # 6 sample users representing distinct user archetypes
        self._users: list[dict[str, Any]] = [
            {
                "id": "1001",
                "username": "alex_builder",
                "name": "Alex Builder",
                "description": "Founder @ AgentRobotics building embodied AI and foundation models for manipulation.",
                "location": "Singapore",
                "followers": 3200,
                "protected": 0,
                "receives_your_dm": True,
            },
            {
                "id": "1002",
                "username": "sarah_robotics",
                "name": "Sarah Chen",
                "description": "Robotics software engineer working on real-time vision-language-action policies.",
                "location": "Vietnam",
                "followers": 1850,
                "protected": 0,
                "receives_your_dm": True,
            },
            {
                "id": "1003",
                "username": "david_closed",
                "name": "David Kim",
                "description": "Researcher in multimodal LLMs and robotic reasoning. DMs closed.",
                "location": "Seoul",
                "followers": 4500,
                "protected": 0,
                "receives_your_dm": False,
            },
            {
                "id": "1004",
                "username": "elena_closed",
                "name": "Elena Rostov",
                "description": "Hardware lead building quadruped robot prototypes in SEA.",
                "location": "Bangkok",
                "followers": 920,
                "protected": 0,
                "receives_your_dm": False,
            },
            {
                "id": "1005",
                "username": "locked_dev",
                "name": "Stealth Engineer",
                "description": "Stealth robotics startup. Tweets protected.",
                "location": "Unknown",
                "followers": 55,
                "protected": 1,
                "receives_your_dm": False,
            },
            {
                "id": "1006",
                "username": "coffee_memes",
                "name": "Coffee Lover",
                "description": "Casual observer, coffee aficionado, posting daily memes.",
                "location": "Hanoi",
                "followers": 210,
                "protected": 0,
                "receives_your_dm": True,
            },
        ]

        # 2-3 sample posts per user
        self._posts: list[dict[str, Any]] = [
            # Posts for 1001 (alex_builder)
            {
                "id": "p_1001_1",
                "author_id": "1001",
                "text": "Just open-sourced our tactile feedback model for robotic grasping. We achieved 94% success on novel objects.",
                "created_at": "2026-11-10T08:00:00Z",
            },
            {
                "id": "p_1001_2",
                "author_id": "1001",
                "text": "Scaling embodied AI requires high-fidelity physical simulation. Benchmarking Isaac Sim vs Genesis.",
                "created_at": "2026-11-11T10:30:00Z",
            },
            # Posts for 1002 (sarah_robotics)
            {
                "id": "p_1002_1",
                "author_id": "1002",
                "text": "Evaluating VLA models on low-cost robot arms in Ho Chi Minh City. Latency is the real bottleneck.",
                "created_at": "2026-11-09T14:15:00Z",
            },
            {
                "id": "p_1002_2",
                "author_id": "1002",
                "text": "Excited to share our technical report on zero-shot generalization across robotic manipulators.",
                "created_at": "2026-11-11T04:20:00Z",
            },
            # Posts for 1003 (david_closed)
            {
                "id": "p_1003_1",
                "author_id": "1003",
                "text": "Our survey on spatial intelligence in large multimodal models is now up on arXiv.",
                "created_at": "2026-11-08T09:00:00Z",
            },
            {
                "id": "p_1003_2",
                "author_id": "1003",
                "text": "Reasoning models are transforming how robots plan multi-step sequential tasks.",
                "created_at": "2026-11-10T12:00:00Z",
            },
            # Posts for 1004 (elena_closed)
            {
                "id": "p_1004_1",
                "author_id": "1004",
                "text": "Field testing quadruped robots across rough outdoor terrain in Chiang Mai.",
                "created_at": "2026-11-07T11:00:00Z",
            },
            # Posts for 1005 (locked_dev)
            {
                "id": "p_1005_1",
                "author_id": "1005",
                "text": "Protected update: testing motor controllers.",
                "created_at": "2026-11-06T15:00:00Z",
            },
            # Posts for 1006 (coffee_memes)
            {
                "id": "p_1006_1",
                "author_id": "1006",
                "text": "Morning espresso hits different on a rainy Tuesday morning.",
                "created_at": "2026-11-11T01:00:00Z",
            },
        ]

    def _check_fail_next(self) -> None:
        """Trigger single simulated failure if set."""
        if self.fail_next:
            exc = self.fail_next
            self.fail_next = None
            raise exc

    def me(self) -> dict[str, str]:
        """Return simulated profile {id, username} and persist to kv['me']."""
        self._check_fail_next()
        result = {"id": "999999", "username": "genaifund_test"}
        kv_set(self.conn, "me", result)
        return result

    def search_recent(self, query: str, max_results: int = 10) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Search sample posts and return matching posts and author users."""
        self._check_fail_next()
        # Return all sample posts and users up to max_results
        posts = self._posts[:max_results]
        users = self._users[:max_results]
        record_usage(self.conn, "post_read", len(posts))
        record_usage(self.conn, "user_read", len(users))
        return posts, users

    def users_by_usernames(self, usernames: list[str]) -> list[dict[str, Any]]:
        """Find sample users matching given usernames (case-insensitive)."""
        self._check_fail_next()
        targets = {u.lstrip("@").lower() for u in usernames}
        matches = [u for u in self._users if u["username"].lower() in targets]
        record_usage(self.conn, "user_read", len(matches))
        return matches

    def following(self, user_id: str, max_results: int = 100) -> list[dict[str, Any]]:
        """Return sample following list."""
        self._check_fail_next()
        users = self._users[:max_results]
        record_usage(self.conn, "user_read", len(users))
        return users

    def user_posts(self, user_id: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Return sample posts for the specified user."""
        self._check_fail_next()
        posts = [p for p in self._posts if p["author_id"] == user_id][:max_results]
        record_usage(self.conn, "post_read", len(posts))
        return posts

    def send_dm(self, user_id: str, text: str) -> dict[str, str]:
        """Record sent message in memory and return fake event and conversation IDs."""
        self._check_fail_next()
        self.sent.append((user_id, text))
        event_id = f"fake_dm_{len(self.sent)}"
        conv_id = f"fake_conv_{user_id}"
        record_usage(self.conn, "dm_send", 1)
        return {"dm_event_id": event_id, "dm_conversation_id": conv_id}

    def dm_events_with(self, user_id: str, max_results: int = 100) -> list[dict[str, Any]]:
        """Return simulated DM events with the specified user."""
        self._check_fail_next()
        events = [e for e in self.inbox if e.get("sender_id") == user_id or e.get("recipient_id") == user_id][
            :max_results
        ]
        record_usage(self.conn, "dm_read", len(events))
        return events

    def dm_events(self, stop_at_id: str | None = None) -> list[dict[str, Any]]:
        """Return simulated DM inbox events, stopping at stop_at_id if provided."""
        self._check_fail_next()
        events: list[dict[str, Any]] = []
        for e in self.inbox:
            if stop_at_id and e.get("id") == stop_at_id:
                break
            events.append(e)
        record_usage(self.conn, "dm_read", len(events))
        return events


def fake_llm(system: str, user: str, schema: dict) -> dict[str, Any]:
    """Mock LLM response conforming to JSON schemas."""
    # Check if this is a score_fit call or draft_dm call based on schema properties
    properties = schema.get("properties", {})
    if "score" in properties:
        return {
            "score": 85,
            "category": "builder",
            "reasons": [
                {
                    "claim": "Building foundation models for robotic manipulation",
                    "source_id": "bio",
                }
            ],
        }
    elif "text" in properties and "evidence" in properties:
        return {
            "text": "Hi Alex, saw your work on open-sourcing the tactile feedback model with 94% success on novel objects. We at GenAI Fund support robotics builders in SEA. Would love to hear what challenges you are facing next?",
            "evidence": [
                {
                    "source_id": "p_1001_1",
                    "quote": "tactile feedback model for robotic grasping",
                }
            ],
        }
    return {}
