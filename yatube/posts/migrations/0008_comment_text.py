# Generated by Django 2.2.16 on 2022-08-27 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220827_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='text',
            field=models.TextField(default=2),
            preserve_default=False,
        ),
    ]
