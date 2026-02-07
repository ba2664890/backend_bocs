# Generated migration for removing sector_health and sector_education roles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fati_accounts', '0001_initial'),
    ]

    operations = [
        # Update the User role field to remove old role choices and add annonceur
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrateur'),
                    ('institution', 'Institution'),
                    ('local_manager', 'Responsable Local'),
                    ('contributor', 'Contributeur'),
                    ('annonceur', 'Annonceur'),
                    ('viewer', 'Lecteur'),
                ],
                default='viewer',
                max_length=20,
                verbose_name='rôle'
            ),
        ),
    ]
