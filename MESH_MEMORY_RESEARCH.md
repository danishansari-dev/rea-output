# Mesh: Persistent Memory Architecture & Cognitive Modeling

## 1. The Problem with Naive Context Windows

Standard LLM companion implementations rely on one of two flawed memory approaches:
1. **Sliding Context Window**: Appending raw chat logs until the token limit is reached, then truncating old messages. This results in total amnesia regarding key user facts established earlier in the relationship.
2. **Naive Vector RAG**: Chunking every single user utterance and storing it in a vector database. This leads to retrieval pollution: querying *"What did I say earlier?"* retrieves irrelevant pleasantries, contradictory past statements, and out-of-date facts.

Rumik AI addresses this with **Mesh**, described publicly as *"a messy memory that knows what to remember and what to forget."*

---

## 2. Theoretical Blueprint of Mesh

Mesh treats memory like human episodic and semantic recall rather than a file archive:

```
                                  [ User Utterance ]
                                          │
                                          ▼
                            ┌───────────────────────────┐
                            │    Salience Evaluator     │
                            │  (Should this be stored?) │
                            └─────────────┬─────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                   No (Ephemeral)                      Yes (Salient)
                        │                                   │
                        ▼                                   ▼
              [ Discard from Mesh ]            ┌─────────────────────────┐
                                               │   Fact Extraction &     │
                                               │   Entity Resolution     │
                                               └────────────┬────────────┘
                                                            │
                                                            ▼
                                               ┌─────────────────────────┐
                                               │ Contradiction Resolver  │
                                               │ (Overwrites old facts)  │
                                               └────────────┬────────────┘
                                                            │
                                                            ▼
                                               ┌─────────────────────────┐
                                               │ Persistent Semantic DB  │
                                               │ (SQLite + BM25/Cosine)  │
                                               └─────────────────────────┘
```

### 2.1. Salience Evaluation (Selective Retention)
Human memory does not record every sentence. It records high-salience moments:
* **High-Salience Indicators**:
  - Personal identity: Name, pronouns, age, birthday, location.
  - Social network: Family members, partners, close friends, pets.
  - Preferences & tastes: Favorite foods, music, hobbies, dislikes.
  - Vulnerabilities & emotional states: Fears, life goals, traumas, proud achievements.
* **Low-Salience Indicators**:
  - Weather observations, transient greetings (*"Good morning"*), transactional confirmations (*"Yes"*, *"Okay"*).

### 2.2. Contradiction Handling & Knowledge Mutation
A major failure mode in conversational AI is asserting outdated facts alongside current facts:
* *User (Turn 10)*: "I work as a software engineer at Google."
* *User (Turn 150)*: "I resigned from Google and started my own AI startup."
* **Naive Retrieval**: Retrieves both facts, causing the companion to ask: *"How is your job at Google and your startup going?"*
* **Mesh Resolution**: Every fact is categorized under an entity/key slot (e.g. `career.current_employer`). When an update occurs, the previous fact is marked as superseded or deleted, updating the user's active state.

### 2.3. Semantic Relevance Ranking & Dynamic Retrieval
When the user speaks, Mesh searches the memory graph using a hybrid scoring formula:
$$\text{Score}(m) = \alpha \cdot \text{Similarity}(q, m) + \beta \cdot \text{Recency}(m) + \gamma \cdot \text{Salience}(m)$$
This ensures that the most pertinent facts are injected into the companion's prompt without consuming excessive context tokens.

### 2.4. User Privacy & Explicit Deletion
True companionship requires trust. Users must be able to inspect what the AI remembers about them and command: *"Forget that I told you about X"*, permanently expunging the record.

---

## 3. Zara's Clean-Room Implementation Plan: ZaraMemoryEngine

Zara's independent memory engine implements all four pillars of the Mesh specification:
* **Persistent Storage**: Robust SQLite schema with indexed tables for `conversation_turns`, `user_facts`, and `emotional_history`.
* **Fact Extractor**: Regex and semantic pattern matching that detects user self-disclosures (*"my name is"*, *"I like"*, *"I feel"*, *"I live in"*, *"I am a"*).
* **Contradiction Resolver**: Overwrites conflicting keys in the `user_facts` table.
* **REST API**: Exposes `/v1/memory` endpoints to list, inspect, and delete stored memories.
