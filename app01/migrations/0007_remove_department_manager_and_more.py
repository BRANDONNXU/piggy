# Generated by Django 4.2.4 on 2023-08-31 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0006_department_manager'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='department',
            name='manager',
        ),
        migrations.AlterField(
            model_name='usersinfo',
            name='create_time',
            field=models.DateField(verbose_name='入职时间'),
        ),
    ]
