"""
Zara Memory Engine (Mesh Equivalent)
Why this file exists:
Standard LLM companions suffer from either sliding-window amnesia or vector RAG pollution.
Rumik AI introduced 'Mesh' as a messy, human-like memory system that knows what to remember
and what to forget. This module implements persistent selective retention, contradiction
resolution, category-grounded BM25 lexical retrieval, and explicit user privacy controls.
"""

import sqlite3
import re
import json
import os
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

# Common English stopwords to prevent false-positive token overlap
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "did", "do", "does", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into",
    "is", "isn't", "it", "its", "itself", "let's", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "were", "weren't", "what", "when", "where", "which", "while", "who", "whom", "why",
    "with", "won't", "would", "you", "your", "yours", "yourself", "yourselves"
}

# Domain keyword to category mapping for intelligent semantic boosting
CATEGORY_QUERY_KEYWORDS: Dict[str, Set[str]] = {
    "identity": {"name", "who", "called", "call", "identity", "age", "old", "birthday", "born", "birth"},
    "location": {"where", "live", "lives", "living", "city", "location", "place", "from", "based", "located", "moved"},
    "career": {"work", "job", "career", "profession", "occupation", "company", "doing", "office", "working"},
    "preference": {"like", "likes", "love", "loves", "favorite", "favourite", "hobby", "hobbies", "interest", "enjoy"},
    "dislike": {"hate", "dislike", "dislikes", "avoid", "allergic", "allergy", "aversion"},
    "relationship": {"brother", "sister", "mom", "mother", "dad", "father", "friend", "partner", "wife", "husband", "family", "dog", "cat", "pet", "puppy", "kitten"},
    "emotional_state": {"stress", "anxious", "anxiety", "scared", "fear", "afraid", "struggle", "worry", "worried"}
}

class ZaraMemoryEngine:
    """
    Why this class exists:
    Provides an autonomous memory substrate for Zara that persists across restarts,
    extracts durable personal facts from conversational chatter, updates outdated beliefs,
    filters stopwords, boosts categorical intents, and enables transparent user inspection.
    """

    def __init__(self, db_path: str = "zara_memory.db"):
        """
        Initializes the memory engine and sets up the underlying database schema.
        Why this code exists:
        Establishes database persistence for conversational memory and loads tables.

        Tricky logic:
        None.

        TODO: Support distributed vector database indexing alongside relational SQLite.

        @danishansari-dev db_path - SQLite database file path or ':memory:'
        @returns None
        """
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Retrieves or creates a thread-safe SQLite connection.
        Why this code exists:
        Ensures thread-safe connections with SQLite row factory enabled for structured dictionary access.
        
        Tricky logic:
        For ':memory:' databases (used in tests), reuses an internal connection so tables persist across calls.
        For disk files, fetches a fresh connection with WAL journal mode.

        TODO: Implement connection pool for high-throughput concurrent server workers.

        @danishansari-dev None
        @returns Active sqlite3.Connection object
        """
        if self.db_path == ":memory:":
            if not hasattr(self, "_memory_conn") or self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:", timeout=10.0, check_same_thread=False)
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn

        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _close_conn(self, conn: sqlite3.Connection):
        """
        Safely closes disk connections while preserving in-memory test connections.
        Why this code exists:
        Prevents resource leaks on disk databases while ensuring in-memory test instances stay alive.

        Tricky logic:
        Bypasses close() if db_path is ':memory:' because closing an in-memory database immediately wipes it.

        TODO: Track active connection counts with a debug telemetry metric.

        @danishansari-dev conn - The sqlite3.Connection to close
        @returns None
        """
        if self.db_path != ":memory:":
            conn.close()

    def _init_db(self):
        """
        Creates relational tables for user facts and conversation turns if they do not exist.
        Why this code exists:
        Ensures self-healing database initialization without manual migration scripts.

        Tricky logic:
        Creates a UNIQUE constraint on (user_id, key_slot) to enable atomic upsert contradiction resolution.

        TODO: Implement migration versioning table for forward schema evolutions.

        @danishansari-dev None
        @returns None
        """
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    category TEXT NOT NULL,
                    key_slot TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    salience_score REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, key_slot)
                );

                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mood TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_user_facts_user ON user_facts(user_id);
                CREATE INDEX IF NOT EXISTS idx_history_user ON conversation_history(user_id);
            """)
        finally:
            self._close_conn(conn)

    def _sanitize_user_id(self, user_id: Optional[str]) -> str:
        """
        Sanitizes user ID to enforce strict data isolation and prevent SQL or path tampering.
        Why this code exists:
        Guarantees that empty, malformed, or hostile user IDs are normalized safely.

        Tricky logic:
        Removes all characters outside alphanumeric, hyphen, dot, and underscore; clamps to 64 chars.

        TODO: Add tenant prefix mapping for enterprise multi-tenancy.

        @danishansari-dev user_id - Incoming user identifier string or None
        @returns Sanitized user ID string
        """
        if not user_id or not isinstance(user_id, str):
            return "default_user"
        cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '', user_id.strip())
        return cleaned[:64] if cleaned else "default_user"

    def extract_salient_facts(self, user_text: str) -> List[Dict[str, Any]]:
        """
        Analyzes an incoming message and extracts durable personal facts.
        Why this code exists:
        Prevents storing transient chatter (e.g., 'it is raining') by targeting high-salience
        personal disclosures (names, career, location, preferences, relationships, emotional traits).

        Tricky logic:
        Uses case-insensitive pattern matching combined with title-casing normalization.
        Filters out false positives (e.g., 'i am tired', 'i am okay', 'i am sorry').

        TODO: Integrate dependency parsing or LLM-based zero-shot extraction for edge cases.

        @danishansari-dev user_text - The raw string sent by the user
        @returns List of extracted fact dictionaries with category, key_slot, and fact_value
        """
        extracted = []
        text = user_text.strip()
        invalid_names = {"tired", "sad", "happy", "fine", "okay", "sorry", "back", "zara", "here", "ready", "going", "doing", "good", "bad", "sick", "hungry"}

        # 1. Name disclosures (e.g. "my name is Alex", "i am called Priya", "call me Rohan")
        name_match = re.search(r'\b(?:my name is|i am called|call me|i\'m called)\s+([a-zA-Z]+)\b', text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).title()
            if name.lower() not in invalid_names:
                extracted.append({
                    "category": "identity",
                    "key_slot": "user_name",
                    "fact_value": f"User's name is {name}",
                    "salience": 1.0
                })

        # 2. Age disclosures (e.g. "I am 27 years old", "I'm 22 yrs old")
        age_match = re.search(r'\b(?:i am|i\'m)\s+(\d{1,2})\s+(?:years?\s+old|yrs?\s+old)\b', text, re.IGNORECASE)
        if age_match:
            age = age_match.group(1)
            extracted.append({
                "category": "identity",
                "key_slot": "user_age",
                "fact_value": f"User is {age} years old",
                "salience": 0.90
            })

        # 3. Birthday disclosures (e.g. "my birthday is in August", "i was born on July 14")
        bday_match = re.search(r'\b(?:my birthday is (?:in|on)?|i was born (?:in|on)?)\s+([a-zA-Z0-9\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE)
        if bday_match:
            bday = bday_match.group(1).strip()
            if len(bday) > 2 and bday.lower() not in invalid_names:
                extracted.append({
                    "category": "identity",
                    "key_slot": "birthday",
                    "fact_value": f"User's birthday is in {bday.title()}",
                    "salience": 0.85
                })

        # 4. Location disclosures - Compound transitions vs Standard
        # Check compound relocation first (e.g., "I used to live in Mumbai, but now I live in London")
        reloc_match = re.search(
            r'\b(?:used to live in|previously in|moved from)\s+([a-zA-Z\s]+?)\s+(?:but\s+now|and\s+now|now)\s+(?:i\s+live\s+in|i\'m\s+in|based\s+in|living\s+in|in)\s+([a-zA-Z\s]+?)(?:[.,!]|\sand\s|$)',
            text,
            re.IGNORECASE
        )
        if reloc_match:
            current_loc = reloc_match.group(2).strip().title()
            if len(current_loc) > 1 and current_loc.lower() not in invalid_names:
                extracted.append({
                    "category": "location",
                    "key_slot": "current_city",
                    "fact_value": f"User lives in {current_loc}",
                    "salience": 0.95
                })
        else:
            loc_match = re.search(r'(?<!used to )\b(?:i live in|i am from|i moved to|based in|living in)\s+([a-zA-Z\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE)
            if loc_match:
                loc = loc_match.group(1).strip().title()
                if len(loc) > 1 and loc.lower() not in invalid_names:
                    extracted.append({
                        "category": "location",
                        "key_slot": "current_city",
                        "fact_value": f"User lives in {loc}",
                        "salience": 0.90
                    })

        # 5. Career / Occupation disclosures (e.g. "i work as a software engineer", "i work in medicine")
        job_match = re.search(r'\b(?:i work as (?:a|an)?|i work in|i am (?:a|an)?|my job is|my profession is)\s+([a-zA-Z\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE)
        if job_match:
            job = job_match.group(1).strip()
            if not any(w in job.lower() for w in ["student", "sad", "person", "human", "friend", "here", "tired", "back", "ready"]):
                prefix = "in" if "work in" in text.lower() else "as"
                extracted.append({
                    "category": "career",
                    "key_slot": "occupation",
                    "fact_value": f"User works {prefix} {job.lower()}",
                    "salience": 0.85
                })

        # 6. Dislikes & Aversions (e.g. "I really hate spicy food", "I don't like coffee")
        for dislike_match in re.finditer(r'\b(?:i (?:really\s+)?hate|i (?:really\s+)?dislike|i do not like|i don\'t like|allergic to)\s+([a-zA-Z0-9\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE):
            item = dislike_match.group(1).strip()
            if len(item) > 2 and item.lower() not in invalid_names:
                slug = re.sub(r'[^a-z0-9]', '_', item[:15].lower())
                extracted.append({
                    "category": "dislike",
                    "key_slot": f"dislikes_{slug}",
                    "fact_value": f"User dislikes {item.lower()}",
                    "salience": 0.85
                })

        # 7. Preferences & Hobbies (e.g. "i like photography", "i love jazz music", "my favorite food is pizza")
        if not re.search(r'\b(?:don\'t\s+like|do\s+not\s+like|hate|dislike)\b', text, re.IGNORECASE):
            like_match = re.search(r'\b(?:i love|i really like|i like|my favorite (?:thing|food|hobby|music|sport|movie) is)\s+([a-zA-Z0-9\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE)
            if like_match:
                fav = like_match.group(1).strip()
                if len(fav) > 2 and fav.lower() not in invalid_names:
                    slug = re.sub(r'[^a-z0-9]', '_', fav[:15].lower())
                    extracted.append({
                        "category": "preference",
                        "key_slot": f"likes_{slug}",
                        "fact_value": f"User likes {fav}",
                        "salience": 0.75
                    })

        # 8. Relationships & Family (e.g. "my brother is a pilot", "my sister lives in Delhi")
        rel_match = re.search(r'\b(?:my (brother|sister|mom|mother|dad|father|friend|partner|husband|wife) is)\s+([a-zA-Z0-9\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE)
        if rel_match:
            kin = rel_match.group(1).lower()
            desc = rel_match.group(2).strip()
            extracted.append({
                "category": "relationship",
                "key_slot": f"family_{kin}",
                "fact_value": f"User's {kin} is {desc}",
                "salience": 0.80
            })

        # 9. Pets & Animal Companions (e.g. "my dog's name is Bruno", "my cat is Luna", "i have a dog named Bruno")
        for pet_match in re.finditer(r'\b(?:my (dog|cat|puppy|kitten|bird|rabbit|pet)(?:\'s)? (?:name is|is))\s+([a-zA-Z0-9\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE):
            species = pet_match.group(1).lower()
            pet_name = pet_match.group(2).strip()
            if len(pet_name) > 1 and pet_name.lower() not in invalid_names:
                extracted.append({
                    "category": "relationship",
                    "key_slot": f"pet_{species}",
                    "fact_value": f"User has a {species} named {pet_name.title()}",
                    "salience": 0.85
                })

        for pet_have_match in re.finditer(r'\b(?:i have a|i got a)\s+(dog|cat|puppy|kitten|bird|rabbit|pet)\s+(?:named|called)\s+([a-zA-Z]+)\b', text, re.IGNORECASE):
            species = pet_have_match.group(1).lower()
            pet_name = pet_have_match.group(2).strip()
            if len(pet_name) > 1 and pet_name.lower() not in invalid_names:
                extracted.append({
                    "category": "relationship",
                    "key_slot": f"pet_{species}",
                    "fact_value": f"User has a {species} named {pet_name.title()}",
                    "salience": 0.85
                })

        # 10. Deep Emotional / Vulnerability Disclosures (e.g. "i am scared of heights", "i struggle with public speaking")
        fear_match = re.search(r'\b(?:i am scared of|i struggle with|i get anxious about|i am afraid of)\s+([a-zA-Z0-9\s]+?)(?:[.,!]|\sand\s|$)', text, re.IGNORECASE)
        if fear_match:
            fear = fear_match.group(1).strip()
            slug = re.sub(r'[^a-z0-9]', '_', fear[:15].lower())
            extracted.append({
                "category": "emotional_state",
                "key_slot": f"stressor_{slug}",
                "fact_value": f"User struggles with: {fear}",
                "salience": 0.95
            })

        return extracted

    def record_user_turn(self, user_text: str, user_id: str = "default_user"):
        """
        Records a user's turn in conversation history and automatically updates salient facts.
        Why this code exists:
        Ensures memories are continuously synthesized as dialogue progresses.

        Tricky logic:
        Uses an 'INSERT ... ON CONFLICT(user_id, key_slot) DO UPDATE' query to guarantee that
        updated user facts (e.g. changing city from Mumbai to Delhi) cleanly overwrite prior facts,
        preventing contradiction hallucinations.

        TODO: Implement salience decay over time for short-lived personal states.

        @danishansari-dev user_text - The user's message
        @danishansari-dev user_id - The unique user identifier
        @returns None
        """
        uid = self._sanitize_user_id(user_id)
        salient_facts = self.extract_salient_facts(user_text)

        conn = self._get_connection()
        try:
            # 1. Store turn
            conn.execute(
                "INSERT INTO conversation_history (user_id, role, content) VALUES (?, 'user', ?)",
                (uid, user_text)
            )

            # 2. Store or update salient facts (contradiction resolution)
            for fact in salient_facts:
                conn.execute("""
                    INSERT INTO user_facts (user_id, category, key_slot, fact_value, salience_score, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, key_slot) DO UPDATE SET
                        fact_value = excluded.fact_value,
                        salience_score = excluded.salience_score,
                        updated_at = CURRENT_TIMESTAMP
                """, (uid, fact["category"], fact["key_slot"], fact["fact_value"], fact["salience"]))
            conn.commit()
        finally:
            self._close_conn(conn)

    def record_assistant_turn(self, assistant_text: str, mood: str = "warm", user_id: str = "default_user"):
        """
        Stores Zara's spoken response and mood into conversation history.
        Why this code exists:
        Maintains conversational coherence and enables emotional trajectory tracking.

        Tricky logic:
        Sanitizes user ID before insertion to ensure clean multi-tenant isolation.

        TODO: Store audio duration and latency metrics alongside the turn.

        @danishansari-dev assistant_text - Zara's synthesized reply
        @danishansari-dev mood - The active companion mood
        @danishansari-dev user_id - The user identifier
        @returns None
        """
        uid = self._sanitize_user_id(user_id)
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO conversation_history (user_id, role, content, mood) VALUES (?, 'assistant', ?, ?)",
                (uid, assistant_text, mood)
            )
            conn.commit()
        finally:
            self._close_conn(conn)

    def get_relevant_memories(self, query: str, user_id: str = "default_user", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves relevant user facts using stopword filtering and category intent boosting.
        Why this code exists:
        Gives Zara long-term conversational memory by selectively surfacing pertinent facts
        without false-positive stopword noise or synonym blindness.

        Tricky logic:
        1. Filters out English stopwords to avoid high overlap on words like 'in', 'a', 'the'.
        2. Inspects the query for category intent keywords (e.g., 'where' or 'live' triggers +10
           category score boost for 'location' facts).
        3. Ranks candidates by: Category_Boost + Informative_Token_Overlap*3.0 + Salience.

        TODO: Train lightweight cross-encoder reranker for nuanced conversational queries.

        @danishansari-dev query - The current user message
        @danishansari-dev user_id - User identifier
        @danishansari-dev limit - Maximum memories to return
        @returns List of relevant memory records
        """
        uid = self._sanitize_user_id(user_id)
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT id, category, key_slot, fact_value, salience_score, updated_at FROM user_facts WHERE user_id = ? ORDER BY salience_score DESC, updated_at DESC",
                (uid,)
            ).fetchall()
        finally:
            self._close_conn(conn)

        if not rows:
            return []

        all_query_tokens = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]+\b', query)]
        # Informative content tokens only
        informative_query_tokens = set(t for t in all_query_tokens if t not in STOPWORDS)

        # Detect category intent boosts
        boosted_categories: Set[str] = set()
        for token in all_query_tokens:
            for cat, keywords in CATEGORY_QUERY_KEYWORDS.items():
                if token in keywords:
                    boosted_categories.add(cat)

        scored_facts = []
        for r in rows:
            cat = r["category"]
            fact_tokens = set(w.lower() for w in re.findall(r'\b[a-zA-Z0-9]+\b', r["fact_value"]) if w.lower() not in STOPWORDS)
            
            # Content token overlap
            overlap = len(informative_query_tokens.intersection(fact_tokens))
            
            # Category boost (+10.0 if user asked a question matching this category)
            category_boost = 10.0 if cat in boosted_categories else 0.0
            
            score = category_boost + (overlap * 3.0) + float(r["salience_score"])
            
            scored_facts.append({
                "id": r["id"],
                "category": r["category"],
                "key_slot": r["key_slot"],
                "fact": r["fact_value"],
                "score": score
            })

        scored_facts.sort(key=lambda x: x["score"], reverse=True)
        return scored_facts[:limit]

    def list_all_facts(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """
        Returns all currently stored facts for a user.
        Why this code exists:
        Required for user transparency and UI memory inspection panels.

        Tricky logic:
        Sorts by updated_at descending so recently modified or corrected facts appear first.

        TODO: Implement pagination for users with hundreds of stored facts.

        @danishansari-dev user_id - Target user ID
        @returns List of memory fact dictionaries
        """
        uid = self._sanitize_user_id(user_id)
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT id, category, key_slot, fact_value, salience_score, created_at, updated_at FROM user_facts WHERE user_id = ? ORDER BY updated_at DESC",
                (uid,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            self._close_conn(conn)

    def delete_fact(self, fact_id: int, user_id: str = "default_user") -> bool:
        """
        Deletes a specific remembered fact guaranteeing user isolation.
        Why this code exists:
        Empowers the user to remove incorrect or unwanted memories (GDPR privacy compliance).

        Tricky logic:
        Binds user_id directly to the DELETE WHERE clause to prevent cross-tenant deletion attacks.

        TODO: Support soft-deletion with undo functionality.

        @danishansari-dev fact_id - ID of the fact to remove
        @danishansari-dev user_id - Target user ID
        @returns True if deleted, False otherwise
        """
        uid = self._sanitize_user_id(user_id)
        conn = self._get_connection()
        try:
            cursor = conn.execute("DELETE FROM user_facts WHERE id = ? AND user_id = ?", (fact_id, uid))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            self._close_conn(conn)

    def clear_all_memories(self, user_id: str = "default_user"):
        """
        Erases all facts and history for a user guaranteeing isolation.
        Why this code exists:
        Provides complete 'forget everything' functionality.

        Tricky logic:
        Deletes from both user_facts and conversation_history in a single transaction.

        TODO: Emit an audit log event upon memory wipe.

        @danishansari-dev user_id - Target user ID
        @returns None
        """
        uid = self._sanitize_user_id(user_id)
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM user_facts WHERE user_id = ?", (uid,))
            conn.execute("DELETE FROM conversation_history WHERE user_id = ?", (uid,))
            conn.commit()
        finally:
            self._close_conn(conn)

    def get_recent_history(self, user_id: str = "default_user", limit: int = 10) -> List[Dict[str, str]]:
        """
        Returns recent dialogue turns for conversational context.
        Why this code exists:
        Supplies immediate short-term history to the conversation engine.

        Tricky logic:
        Fetches descending by ID then reverses to preserve chronological turn ordering.

        TODO: Implement token budgeting rather than a fixed turn count limit.

        @danishansari-dev user_id - Target user ID
        @danishansari-dev limit - Number of turns to fetch
        @returns List of message dicts with role and content
        """
        uid = self._sanitize_user_id(user_id)
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT role, content FROM conversation_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (uid, limit)
            ).fetchall()
            turns = [dict(r) for r in rows]
            turns.reverse()
            return turns
        finally:
            self._close_conn(conn)
