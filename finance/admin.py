from django.contrib import admin

# Register your models here.
from .models import Category, Transaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["date", "type", "amount", "category", "description"]
    list_filter = ["type", "category"]
    search_fields = ["description"]