"""Filters."""
import django_filters

from threads.weave.models import Message, Person, Thread


class PersonFilter(django_filters.FilterSet):
    """Person filter."""

    class Meta:
        """Filter options."""

        model = Person
        fields = "__all__"


class ThreadFilter(django_filters.FilterSet):
    """Thread filter."""

    class Meta:
        """Filter options."""

        model = Thread
        fields = "__all__"


class MessageFilter(django_filters.FilterSet):
    """Message filter."""

    class Meta:
        """Filter options."""

        model = Message
        fields = "__all__"
