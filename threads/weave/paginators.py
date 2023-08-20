"""Paginator."""
from django.core.paginator import Paginator
from django.db import (
    DEFAULT_DB_ALIAS,
    DatabaseError,
    OperationalError,
    connection,
    transaction,
)
from django.db.models import Count
from django.utils.functional import cached_property
from rest_framework.pagination import PageNumberPagination


class CustomPaginator(Paginator):
    """Custom Paginator."""

    @cached_property
    def count(self) -> int:
        """Return an estimate of the total number of objects."""
        # First try running the normal COUNT(*)
        with transaction.atomic(), connection.cursor() as cursor:
            try:
                cursor.execute("SET LOCAL statement_timeout TO 10;")
                return super().count
            except (OperationalError, DatabaseError):
                pass

        # Return the estimate instead
        # This is * VERY * hacky btw
        with connection.cursor() as cursor:
            db_table = self.object_list.model._meta.db_table
            query = (
                self.object_list.annotate(__count=Count("*"))
                .values("__count")
                .order_by()
                .query
            )
            query.group_by = None
            sql, params = query.get_compiler(DEFAULT_DB_ALIAS).as_sql()
            sql = sql.replace(
                f'FROM "{db_table}"',
                f'FROM "{db_table}" TABLESAMPLE BERNOULLI (10) REPEATABLE (42)',
            )
            cursor.execute(sql, params)
            return 10 * int(cursor.fetchone()[0])


class CustomPageNumberPagination(PageNumberPagination):
    """Custom page number pagination."""

    django_paginator_class = CustomPaginator
