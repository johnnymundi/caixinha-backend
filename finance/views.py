from django.shortcuts import render
from datetime import date as date_cls
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer

def parse_month(month_str: str | None) -> tuple[int, int]:
    """
    month_str: 'YYYY-MM'
    """
    today = date_cls.today()
    if not month_str:
        return today.year, today.month

    # tenta montar uma data do primeiro dia do mês
    d = parse_date(month_str + "-01")
    if not d:
        return today.year, today.month
    return d.year, d.month

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related("category").all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["type", "category"]
    search_fields = ["description"]
    ordering_fields = ["date", "amount", "id", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        month = self.request.query_params.get("month")  # YYYY-MM
        if month:
            y, m = parse_month(month)
            qs = qs.filter(date__year=y, date__month=m)
        return qs

    @action(detail=False, methods=["get"], url_path="recent")
    def recent(self, request):
        limit = int(request.query_params.get("limit", "10"))
        qs = self.get_queryset().order_by("-date", "-id")[: max(1, min(limit, 50))]
        data = TransactionSerializer(qs, many=True).data
        return Response(data)


class SummaryView(APIView):
    def get(self, request):
        month = request.query_params.get("month")  # YYYY-MM
        y, m = parse_month(month)

        month_qs = Transaction.objects.filter(date__year=y, date__month=m)

        income = month_qs.filter(type=Transaction.Type.INCOME).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]
        expense = month_qs.filter(type=Transaction.Type.EXPENSE).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]

        total_income = Transaction.objects.filter(type=Transaction.Type.INCOME).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]
        total_expense = Transaction.objects.filter(type=Transaction.Type.EXPENSE).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]

        by_category = (
            month_qs.values("category__id", "category__name", "type")
            .annotate(total=Coalesce(Sum("amount"), Decimal("0.00")))
            .order_by("type", "category__name")
        )

        return Response(
            {
                "month": f"{y:04d}-{m:02d}",
                "income": income,
                "expense": expense,
                "balance_month": income - expense,
                "balance_total": total_income - total_expense,
                "by_category": list(by_category),
            }
        )