"""Paginator."""
from django.core.paginator import Paginator
from django.db import connection
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination


class CustomPaginator(Paginator):
    """Custom Paginator."""

    @cached_property
    def count(self) -> int:
        """Return the total number of objects, across all pages."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT reltuples FROM pg_class WHERE relname = %s",
                [self.object_list.query.model._meta.db_table],
            )
            return int(cursor.fetchone()[0])


class CustomPageNumberPagination(PageNumberPagination):
    """Custom page number pagination."""

    django_paginator_class = CustomPaginator
