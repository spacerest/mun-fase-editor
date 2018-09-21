# Generated by Django 2.1.1 on 2018-09-20 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0008_auto_20180919_1805'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreviewImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='preview')),
                ('date_updated', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='SavedImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='final')),
                ('selfie_user', models.CharField(default='@mun_fases', max_length=60)),
                ('background_user', models.CharField(blank=True, max_length=60, null=True)),
                ('background_description', models.CharField(default=':)', max_length=60)),
                ('foreground_user', models.CharField(blank=True, max_length=60, null=True)),
                ('foreground_description', models.CharField(default=':)', max_length=60)),
                ('percent_illuminated', models.IntegerField()),
            ],
        ),
        migrations.AlterField(
            model_name='moonimage',
            name='image',
            field=models.ImageField(upload_to='moon'),
        ),
        migrations.AlterField(
            model_name='selfieimage',
            name='image',
            field=models.ImageField(upload_to='selfie'),
        ),
        migrations.AlterField(
            model_name='textureimage',
            name='image',
            field=models.ImageField(upload_to='texture'),
        ),
        migrations.AlterField(
            model_name='textureimage',
            name='username',
            field=models.CharField(default='none', max_length=50),
        ),
    ]
