import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from api.models import Ingredient


class Command(BaseCommand):
    help = """Load ingredients from csv file to bd.
            For positional argument 'path' use relative path"""

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        data_file = Path(options['path'])
        try:
            with data_file.open('r') as file:
                reader = csv.reader(file)
                for row in reader:
                    try:
                        Ingredient.objects.create(
                            name=row[0],
                            measurement_unit=row[1]
                        )
                    except IntegrityError:
                        self.stdout.write(f'Ingredient "{row[0]}" exist')
        except FileNotFoundError:
            raise CommandError('File not found')
        self.stdout.write('Data loaded successfully')
