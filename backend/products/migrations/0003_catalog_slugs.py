from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    alias = schema_editor.connection.alias
    for name in ("Category", "Product"):
        model = apps.get_model("products", name)
        records = model.objects.using(alias)
        for record in records.only("pk", "name").iterator():
            base = slugify(record.name.replace("ı", "i").replace("İ", "I"))[:200] or "kayit"
            records.filter(pk=record.pk).update(slug=f"{base}-{record.pk}")


class Migration(migrations.Migration):
    dependencies = [("products", "0002_remove_product_price")]
    operations = [
        migrations.AddField(
            model_name="category", name="slug",
            field=models.SlugField(max_length=220, null=True, editable=False, db_index=False),
        ),
        migrations.AddField(
            model_name="product", name="slug",
            field=models.SlugField(max_length=220, null=True, editable=False, db_index=False),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="category", name="slug",
            field=models.SlugField(max_length=220, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="product", name="slug",
            field=models.SlugField(max_length=220, unique=True, editable=False),
        ),
    ]
