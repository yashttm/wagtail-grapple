# Generated by Django 2.2.1 on 2019-08-24 11:22

from django.db import migrations
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_blogpage_example_rich_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpage',
            name='example_rich_text',
            field=wagtail.core.fields.RichTextField(),
        ),
    ]