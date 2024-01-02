# Generated by Django 4.2.4 on 2023-09-20 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saas', '0011_projectinvite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectinvite',
            name='period',
            field=models.IntegerField(blank=True, choices=[(30, '30分钟'), (60, '1小时'), (360, '6小时'), (1440, '24小时')], default=1440, null=True, verbose_name='有效期'),
        ),
    ]
