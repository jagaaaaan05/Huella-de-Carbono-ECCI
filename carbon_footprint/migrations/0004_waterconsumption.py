from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carbon_footprint', '0003_calculationrun_carbon_foot_period__f64ceb_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaterConsumption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=150, null=True)),
                ('m3', models.FloatField()),
                ('total_tco2e', models.FloatField(blank=True, null=True)),
                ('campus', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='water_records',
                    to='carbon_footprint.campus',
                )),
                ('emission_factor', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='water_usages',
                    to='carbon_footprint.emissionfactor',
                )),
                ('period', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='water_records',
                    to='carbon_footprint.period',
                )),
            ],
        ),
    ]
