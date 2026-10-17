"""
Zara Agent & Companion Persona Interface
Why this file exists:
Provides a backwards-compatible entry point for companion dialogue by wrapping
ZaraConversationEngine, ensuring existing references to ZaraCompanion continue to work seamlessly.
"""

from zara.conversation_engine import ZaraConversationEngine, ZARA_CORE_PROMPT
from zara.memory_engine import ZaraMemoryEngine
from zara.context_engine import ZaraContextEngine

class ZaraCompanion(ZaraConversationEngine):
    """
    Why this class exists:
    Maintains compatibility with early prototypes while inheriting the full
    cognitive abilities of ZaraConversationEngine.
    """
    def __init__(self, name: str = "Zara", persona_style: str = "empathetic"):
        """
        Initializes the legacy companion wrapper.
        Why this code exists:
        Maintains compatibility with legacy prototype configurations.

        Tricky logic:
        Calls super().__init__() to wire up memory and context engines.

        TODO: Deprecate once all callers migrate to ZaraConversationEngine.

        @danishansari-dev name - Companion name
        @danishansari-dev persona_style - Persona style string
        @returns None
        """
        super().__init__()
        self.name = name
        self.persona_style = persona_style

    async def generate_reply(self, user_message: str, user_id: str = "default_user"):
        """
        Generates a companion reply dictionary.
        Why this code exists:
        Provides the legacy signature expected by initial routes.

        Tricky logic:
        Forwards directly to generate_response() in the parent class.

        TODO: Add parameter deprecation warning telemetry.
        
        @danishansari-dev user_message - User's incoming text
        @danishansari-dev user_id - Unique user ID
        @returns Dict with text, mood, source, and context
        """
        return await self.generate_response(user_message, user_id=user_id)
