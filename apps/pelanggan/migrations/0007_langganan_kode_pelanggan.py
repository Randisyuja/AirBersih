from django.db import migrations, models


def backfill_langganan_kode_pelanggan(apps, schema_editor):
    Langganan = apps.get_model("pelanggan", "Langganan")
    for langganan in Langganan.objects.filter(kode_pelanggan__isnull=True):
        langganan.kode_pelanggan = f"MBR{langganan.pk:05d}"
        langganan.save(update_fields=["kode_pelanggan"])


class Migration(migrations.Migration):

    dependencies = [
        ("pelanggan", "0006_pelanggan_barcode"),
    ]

    operations = [
        migrations.AddField(
            model_name="langganan",
            name="kode_pelanggan",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=64,
                null=True,
                unique=True,
                verbose_name="Kode Member / Pelanggan",
            ),
        ),
        migrations.RunPython(
            backfill_langganan_kode_pelanggan,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
