import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

from api.models import Ingredient


class Command(BaseCommand):
    help = """Load ingredients from csv file to bd.
            For positional argument 'path' use relative path"""

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        data_file = Path(options['path'])
        ingredients = []
        try:
            with data_file.open('r') as file:
                reader = csv.reader(file)
                for row in reader:
                    obj = Ingredient(name=row[0], measurement_unit=row[1])
                    ingredients.append(obj)
                Ingredient.objects.bulk_create(ingredients)
                self.stdout.write('Data loaded successfully')
        except FileNotFoundError:
            raise CommandError('File not found')
