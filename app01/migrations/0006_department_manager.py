# Generated by Django 4.2.4 on 2023-08-29 23:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0005_remove_department_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app01.usersinfo', verbose_name='部门经理'),
        ),
    ]
