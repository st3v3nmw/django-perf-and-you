"""Models."""
from django.db import models
from django.db.models import Index, Q
from django.utils.functional import cached_property


class AbstractBase(models.Model):
    """Abstract Base."""

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(db_index=True)

    class Meta:
        """Model options."""

        ordering = ("-updated",)
        abstract = True


class Person(AbstractBase):
    """Person Model."""

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email_address = models.EmailField(unique=True)

    @cached_property
    def full_name(self) -> str:
        """Person's full name."""
        return f"{self.first_name} {self.last_name}"


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

    class Meta(AbstractBase.Meta):
        """Model options."""

        indexes = [
            Index(
                fields=["deleted"],
                name="soft_deletes_ignore",
                condition=Q(deleted=False),
            )
        ]
