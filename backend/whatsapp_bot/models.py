from django.db import models


class WhatsappConversation(models.Model):
    """Conversation state for a WhatsApp user (by WA id / phone).

    Keep this minimal; it's used to provide short conversational context to the AI.
    """

    wa_id = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.wa_id


class WhatsappMessage(models.Model):
    ROLE_CHOICES = (
        ("user", "user"),
        ("assistant", "assistant"),
        ("system", "system"),
    )

    conversation = models.ForeignKey(WhatsappConversation, related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.conversation.wa_id} {self.role}: {self.content[:40]}"
