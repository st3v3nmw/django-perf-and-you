"""Paginator."""
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination


class CustomPaginator(Paginator):
    """Custom Paginator."""

    @cached_property
    def count(self) -> int:
        """Return an estimate of the total number of objects.

        Could be made more robust by first running the normal COUNT(*)
        with a `SET LOCAL statement_timeout TO 50`
        and then reverting to this if that doesn't complete in time.
        """
        with connection.cursor() as cursor:
            db_table = self.object_list.model._meta.db_table
            query = (
                self.object_list.annotate(__count=Count("*"))
                .values("__count")
                .order_by()
                .query
            )
            query.group_by = None
            query_string = str(query)
            query_string = query_string.replace(
                f'FROM "{db_table}"',
                f'FROM "{db_table}" TABLESAMPLE BERNOULLI (10) REPEATABLE (42)',
            )
            cursor.execute(query_string)
            return 10 * int(cursor.fetchone()[0])


class CustomPageNumberPagination(PageNumberPagination):
    """Custom page number pagination."""

    django_paginator_class = CustomPaginator
