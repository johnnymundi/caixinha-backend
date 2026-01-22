'''finance.views'''
from datetime import date as date_cls
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

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
    '''
    Docstring for CategoryViewSet
    '''
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return (
            Category.objects
            .filter(Q(user__isnull=True) | Q(user=self.request.user))
            .order_by("name")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        ''' Se deletar categoria em uma transação, joga para "Outros" '''
        instance = self.get_object()
    
        outros, _ = Category.objects.get_or_create(user=None, name="Outros")

        # Protegendo a categoria mor 'Outros'
        if instance.name.strip().lower() == "outros":
            return Response({"detail": "A categoria 'Outros' não pode ser excluída."}, status=status.HTTP_409_CONFLICT)

        # Joga pra 'Outros' quando a categoria é deletada
        Transaction.objects.filter(user=request.user,category=instance).update(category=outros)

        return super().destroy(request, *args, **kwargs)

class TransactionViewSet(viewsets.ModelViewSet):
    '''
    Docstring for TransactionViewSet
    '''
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.select_related("category").all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["type", "category"]
    search_fields = ["description"]
    ordering_fields = ["date", "amount", "id", "created_at"]

    def get_queryset(self):
        '''
        Docstring for get_queryset
        
        :param self: Description
        '''
        qs = Transaction.objects.filter(user=self.request.user)
        month = self.request.query_params.get("month")
        if month:
            # month = "YYYY-MM"
            year, m = month.split("-")
            qs = qs.filter(date__year=int(year), date__month=int(m))

        tx_type = self.request.query_params.get("type")
        if tx_type in ("IN", "OUT"):
            qs = qs.filter(type=tx_type)

        category = self.request.query_params.get("category")
        if category and category.isdigit():
            qs = qs.filter(category_id=int(category))

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="recent")
    def recent(self, request):
        '''
        Docstring for recent
        
        :param self: Description
        :param request: Description
        '''
        limit = int(request.query_params.get("limit", "10"))
        qs = self.get_queryset().order_by("-date", "-id")[: max(1, min(limit, 50))]
        data = TransactionSerializer(qs, many=True).data
        return Response(data)

class SummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = request.query_params.get("month")  # YYYY-MM
        y, m = parse_month(month)

        base_qs = Transaction.objects.filter(user=request.user)

        month_qs = base_qs.filter(date__year=y, date__month=m)

        income = month_qs.filter(type=Transaction.Type.INCOME).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]

        expense = month_qs.filter(type=Transaction.Type.EXPENSE).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]

        total_income = base_qs.filter(type=Transaction.Type.INCOME).aggregate(
            v=Coalesce(Sum("amount"), Decimal("0.00"))
        )["v"]

        total_expense = base_qs.filter(type=Transaction.Type.EXPENSE).aggregate(
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