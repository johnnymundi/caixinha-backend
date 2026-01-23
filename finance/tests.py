# finance/tests.py
import pytest
from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from finance.models import Category, Transaction


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username="john", email="john@test.com", password="12345678")


@pytest.fixture
def other_user():
    User = get_user_model()
    return User.objects.create_user(username="mary", email="mary@test.com", password="12345678")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def _category_list_url():
    # Se seu router for: router.register("categories", CategoryViewSet)
    # o basename padrão vira "category" -> "category-list"
    #
    # Se você usou basename="categories", então seria "categories-list".
    return reverse("category-list")


def _category_detail_url(pk: int):
    return reverse("category-detail", kwargs={"pk": pk})


def test_list_returns_global_and_user_categories_only(auth_client, user, other_user):
    Category.objects.create(user=None, name="Alimentação")
    Category.objects.create(user=None, name="Transporte")
    Category.objects.create(user=None, name="Outros")

    Category.objects.create(user=user, name="Lazer")
    Category.objects.create(user=other_user, name="Investimentos")

    resp = auth_client.get(_category_list_url())
    assert resp.status_code == 200

    data = resp.json()
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    names = [item["name"] for item in items]

    assert "Alimentação" in names
    assert "Transporte" in names
    assert "Outros" in names
    assert "Lazer" in names
    assert "Investimentos" not in names

    assert names == sorted(names)

def test_create_category_sets_user(auth_client, user):
    resp = auth_client.post(_category_list_url(), data={"name": "Mercado"}, format="json")
    assert resp.status_code == 201

    cat_id = resp.json()["id"]
    cat = Category.objects.get(id=cat_id)
    assert cat.user == user
    assert cat.name == "Mercado"

def test_create_category_outros_is_reserved(auth_client):
    resp = auth_client.post(_category_list_url(), data={"name": "Outros"}, format="json")
    assert resp.status_code == 400
    body = resp.json()
    # validate_name -> erro em "name"
    assert "name" in body

def test_destroy_category_moves_user_transactions_to_global_outros(auth_client, user):
    outros, _ = Category.objects.get_or_create(user=None, name="Outros")
    cat = Category.objects.create(user=user, name="Lazer")

    tx = Transaction.objects.create(
        user=user,
        type=Transaction.Type.EXPENSE,
        amount=Decimal("10.00"),
        date=date(2026, 1, 1),
        description="Teste",
        category=cat,
    )

    resp = auth_client.delete(_category_detail_url(cat.id))
    assert resp.status_code == 204

    tx.refresh_from_db()
    assert tx.category_id == outros.id

    assert not Category.objects.filter(id=cat.id).exists()

def test_destroy_outros_returns_409_and_does_not_delete(auth_client):
    outros, _ = Category.objects.get_or_create(user=None, name="Outros")

    resp = auth_client.delete(_category_detail_url(outros.id))
    assert resp.status_code == 409

    assert Category.objects.filter(id=outros.id).exists()