"""Serializers."""
from rest_framework import serializers

from threads.weave.models import Message, Person, Thread


class PersonSerializer(serializers.ModelSerializer):
    """Person serializer."""

    class Meta:
        """Serializer options."""

        model = Person
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    """Message serializer."""

    sender = serializers.ReadOnlyField(source="sent_by.full_name")

    class Meta:
        """Serializer options."""

        model = Message
        fields = "__all__"


class ThreadSerializer(serializers.ModelSerializer):
    """Thread serializer."""

    messages = MessageSerializer(many=True)

    class Meta:
        """Serializer options."""

        model = Thread
        fields = "__all__"
