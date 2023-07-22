from django.contrib import admin
from django.contrib.auth import get_user_model

from api import models


User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'last_name', 'first_name', 'email')
    list_filter = ('email', 'first_name')
    search_fields = ('last_name__startswith', 'first_name__startswith')


@admin.register(models.UserFollowing)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following_user')


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )
    search_fields = ('name__startswith', )


@admin.register(models.IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount')


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name')
    list_filter = ('author', 'name', 'tags')
    fields = ('author', 'name', 'image', 'cooking_time', 'tags', 'favorite')
    readonly_fields = ('favorite', )

    def favorite(self, obj):
        result = obj.favorited_for.count()
        return result
