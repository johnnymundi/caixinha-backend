'''finance/models.py'''
from django.conf import settings
from django.db import models

class Category(models.Model):
    '''
    Model de categoria da caixinha
    '''
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")

    class Meta:
        '''
        Docstring for Meta
        '''
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return self.name
    
class Transaction(models.Model):
    ''' Model de Transaction'''
    class Type(models.TextChoices):
        ''' Types '''
        INCOME = "IN", "Entrada"
        EXPENSE = "OUT", "Saída"

    type = models.CharField(max_length=3, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self) -> str:
        return f"{self.get_type_display()} R$ {self.amount} em {self.date}"