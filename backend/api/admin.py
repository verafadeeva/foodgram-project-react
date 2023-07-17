from django.contrib import admin
from django.contrib.auth import get_user_model

from api import models


User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(models.UserFollowing)
class UserFollowAdmin(admin.ModelAdmin):
    pass


@admin.register(models.RoleUser)
class RoleUSerAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass


@admin.register(models.IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    pass
