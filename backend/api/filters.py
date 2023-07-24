from django_filters import rest_framework as filters
from api import models


class RecipeFilter(filters.FilterSet):
    author__id = filters.NumberFilter()
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=models.Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = models.Recipe
        fields = ['author', 'tags']

    def get_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return self.request.user.favorite_list.all()
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return self.request.user.shopping_list.all()
        return queryset
