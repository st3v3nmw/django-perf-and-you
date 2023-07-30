"""Models."""
import uuid

from django.db import models


class AbstractBase(models.Model):
    """Abstract Base."""

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField()

    class Meta:
        """Model options."""

        ordering = ("-updated",)
        abstract = True


class Person(AbstractBase):
    """Person Model."""

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email_address = models.EmailField(unique=True)


class Thread(AbstractBase):
    """Thread Model."""

    title = models.CharField(max_length=64)


class Message(AbstractBase):
    """Message Model."""

    text = models.TextField()
    sent_by = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="messages",
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.PROTECT,
        related_name="messages",
    )