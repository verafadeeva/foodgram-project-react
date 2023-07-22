from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


def user_directory_path(instance, filename):
    return "user_{0}/{1}".format(instance.author.id, filename)


class Profile(AbstractUser):
    favorite_list = models.ManyToManyField(
        'Recipe',
        related_name='favorited_for',
        blank=True,
    )
    shopping_list = models.ManyToManyField(
        'Recipe',
        related_name='added_to_cart',
        blank=True,
    )

    def __str__(self):
        return f'{self.username}'

    def get_absolute_url(self):
        return reverse("profile", kwargs={"pk": self.pk})


class UserFollowing(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    following_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "following_user"),
                                    name="unique_followers")
        ]

    def __str__(self):
        return f'{self.user} follows {self.following_user}'

    def get_absolute_url(self):
        return reverse("follow", kwargs={"pk": self.pk})


class Tag(models.Model):
    name = models.CharField(
        max_length=10,
        unique=True,
    )
    color = models.CharField(
        max_length=7,
        unique=True,
    )
    slug = models.SlugField(
        unique=True,
    )

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse("tags", kwargs={"pk": self.pk})


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=20)

    class Meta:
        ordering = ("name", )
        indexes = [
            models.Index(fields=("name", ), name="ingredient_name_idx")
        ]
        constraints = [
            models.UniqueConstraint(fields=("name", "measurement_unit"),
                                    name="unique_ingridient")
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

    def get_absolute_url(self):
        return reverse("ingredients", kwargs={"pk": self.pk})


class Recipe(models.Model):
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    name = models.CharField(
        max_length=200,
    )
    image = models.ImageField(
        upload_to=user_directory_path,
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientAmount",
    )
    tags = models.ManyToManyField(Tag)
    cooking_time = models.IntegerField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pub_date", )

    def __str__(self):
        return f'{self.name}: Автор: {self.author.username}'

    def get_absolute_url(self):
        return reverse("recipes", kwargs={"pk": self.pk})


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("ingredient", "recipe"),
                                    name="ingredient_for_recipe")
        ]
