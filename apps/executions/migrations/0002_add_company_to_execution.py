from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('executions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='execution',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='executions',
                to='authentication.company',
            ),
        ),
    ]
