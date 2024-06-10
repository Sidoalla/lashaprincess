# Generated by Django 5.0.6 on 2024-06-02 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prenotazioni', '0002_prenotazione_consent_timestamp'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='prenotazione',
            options={'permissions': [('can_edit_prenotazione', 'Can edit prenotazione'), ('can_delete_prenotazione', 'Can delete prenotazione')]},
        ),
        migrations.AddField(
            model_name='prenotazione',
            name='artista',
            field=models.CharField(default='Artista sconosciuto', max_length=100),
        ),
    ]
