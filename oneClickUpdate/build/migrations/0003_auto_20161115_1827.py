# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-15 12:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('build', '0002_auto_20161114_1544'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='capablities',
            options={'permissions': (('can_create_build', 'Create Normal Build'), ('can_create_revertbuild', 'Create Revert Build'), ('can_view_buildhistory', 'View Build History'), ('can_manage_buildengine', 'Manage Build Engine'), ('can_view_statstics', 'View Statstics'), ('can_view_and_write', 'Can view and write'))},
        ),
    ]