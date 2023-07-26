import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from api.models import Tag


class Command(BaseCommand):
    help = """Load tags from csv file to bd.
            For positional argument 'path' use relative path"""

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        data_file = Path(options['path'])
        tags = []
        try:
            with data_file.open('r') as file:
                reader = csv.reader(file)
                for row in reader:
                    tag = Tag(name=row[0], color=row[1], slug=row[2])
                    tags.append(tag)
                try:
                    Tag.objects.bulk_create(tags)
                    self.stdout.write('Data loaded successfully')
                except IntegrityError:
                    self.stdout.write(f'"{tag.name}" exist')
        except FileNotFoundError:
            raise CommandError('File not found')
