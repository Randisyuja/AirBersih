from django.db import migrations, models


def backfill_pelanggan_barcodes(apps, schema_editor):
    Pelanggan = apps.get_model('pelanggan', 'Pelanggan')
    for p in Pelanggan.objects.all():
        if not p.barcode:
            p.barcode = f"PLG{p.id_pelanggan:05d}"
            p.save(update_fields=['barcode'])


def reverse_backfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pelanggan', '0005_alter_tagihan_jumlah_bayar_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pelanggan',
            name='barcode',
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=64,
                null=True,
                unique=True,
                verbose_name='Barcode / Kode Pelanggan'
            ),
        ),
        migrations.RunPython(
            backfill_pelanggan_barcodes,
            reverse_code=reverse_backfill
        ),
    ]
