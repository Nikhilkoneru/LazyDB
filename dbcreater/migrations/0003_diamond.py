# Generated by Django 2.2.6 on 2019-10-25 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbcreater', '0002_diamond'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesjancsv',
            name='account_created',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='country',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='last_login',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='latitude',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='longitude',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='payment_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='price',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='product',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='salesjancsv',
            name='transaction_date',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
