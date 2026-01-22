from django.db import migrations

def create_default_category(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    Category.objects.get_or_create(name="Outros")

def reverse(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    Category.objects.filter(name="Outros").delete()

class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_category, reverse),
    ]
