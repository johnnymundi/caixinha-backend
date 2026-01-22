from rest_framework import serializers
from .models import Category, Transaction

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "date",
            "description",
            "category",
            "category_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "category_name"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value
    
    def _get_default_category(self):
        # Garante fallback "Outros"
        cat, _ = Category.objects.get_or_create(name="Outros")
        return cat

    def validate(self, attrs):
        """
        Se category vier null (ou não vier), define "Outros".
        IMPORTANTE: em PATCH, attrs pode não ter 'category', então só aplica fallback
        quando:
          - é create (self.instance is None), ou
          - o cliente explicitamente enviou category=null
        """
        if self.instance is None:
            # CREATE: se não mandou category, ou mandou null => "Outros"
            if attrs.get("category", None) is None:
                attrs["category"] = self._get_default_category()
        else:
            # UPDATE/PATCH: só troca pra "Outros" se o cliente mandou explicitamente category=null
            if "category" in attrs and attrs["category"] is None:
                attrs["category"] = self._get_default_category()

        return attrs
