import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from products.models import Category, Product


class Command(BaseCommand):
    help = "Mevcut ürün ve kategorileri görselli örnek katalogla değiştirir."

    def add_arguments(self, parser):
        parser.add_argument("--replace", action="store_true", help="Mevcut kataloğu değiştir.")

    def handle(self, *args, **options):
        if not options["replace"]:
            raise CommandError("Mevcut kataloğu değiştirmek için --replace kullanın.")

        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "demo_catalog.json"
        asset_dir = fixture.parent / "images"
        catalog = json.loads(fixture.read_text(encoding="utf-8"))
        entries = catalog["categories"] + catalog["products"]
        images = {entry["image"]: asset_dir / entry["image"] for entry in entries}
        for image in images.values():
            if not image.is_file():
                raise CommandError(f"Görsel bulunamadı: {image}")

        created_images = []

        def save_record(record, filename):
            with images[filename].open("rb") as source:
                record.image = File(source, name=filename)
                try:
                    record.save()
                finally:
                    if record.image and record.image._committed:
                        created_images.append((record.image.storage, record.image.name))
            return record

        try:
            with transaction.atomic():
                _, deleted = Category.objects.all().delete()
                categories = {}
                for entry in catalog["categories"]:
                    fields = {key: value for key, value in entry.items() if key != "image"}
                    category = save_record(Category(**fields), entry["image"])
                    categories[category.slug] = category

                for entry in catalog["products"]:
                    fields = {key: value for key, value in entry.items() if key not in ("image", "category")}
                    save_record(Product(category=categories[entry["category"]], **fields), entry["image"])
        except Exception:
            # If the transaction did not commit, remove only newly written files.
            for storage, name in created_images:
                if not Category.objects.filter(image=name).exists() and not Product.objects.filter(image=name).exists():
                    storage.delete(name)
            raise

        self.stdout.write(self.style.SUCCESS(
            f'Silinen: {deleted.get("products.Category", 0)} kategori ve '
            f'{deleted.get("products.Product", 0)} ürün. '
            f'Eklenen: {len(categories)} kategori ve {len(catalog["products"])} ürün.'
        ))
