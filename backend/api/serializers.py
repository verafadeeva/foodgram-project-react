import base64
from time import time

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers

from api import models


User = get_user_model()


class ProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        following = user.following.filter(following_user=obj)
        return True if following else False


class ProfileCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'password')


class RecipeFieldSerializer(serializers.RelatedField):
    def to_representation(self, value):
        data = {
            'id': value.id,
            'name': value.name,
            'image': value.image.url,
            'cooking_time': value.cooking_time
        }
        return data


class SubscriptionsSerializer(ProfileSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipes'] = RecipeFieldSerializer(
            many=True, read_only=True)
        self.fields['recipes_count'] = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        count = obj.recipes.all().count()
        return count


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'

    def to_internal_value(self, data):
        tag = get_object_or_404(models.Tag, id=data)
        return tag


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    measurement_unit = serializers.CharField(read_only=True)

    class Meta:
        model = models.Ingredient
        fields = '__all__'


class IngredientAmountSerializer(IngredientSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'] = serializers.SerializerMethodField()

    def get_amount(self, obj):
        recipe_id = self.context.get('view').kwargs.get('pk')
        if recipe_id is None:
            amount = obj.ingredientamount_set.all()[0].amount
        else:
            amount = obj.ingredientamount_set.get(recipe__id=recipe_id).amount
        return amount

    def to_internal_value(self, data):
        ing_id = data.pop('id')
        ingredient = get_object_or_404(models.Ingredient, id=ing_id)
        data['ingredient'] = ingredient
        return data


class ImageFieldSerialiser(serializers.ImageField):
    def to_internal_value(self, data):
        img = base64.b64decode(data)
        name = f'{int(time())}.jpeg'
        with open(name, 'wb') as file:
            file.write(img)
        return name


class RecipeSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(many=True)
    image = ImageFieldSerialiser()
    cooking_time = serializers.IntegerField(min_value=1)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        favorited_for = obj.favorited_for.all()
        return True if user in favorited_for else False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        added_to_cart = obj.added_to_cart.all()
        return True if user in added_to_cart else False

    def create(self, validate_data):
        author = self.context.get('request').user
        tags = validate_data.pop('tags')
        ingredients = validate_data.pop('ingredients')
        instance, _ = models.Recipe.objects.get_or_create(
            author=author, **validate_data
        )
        instance.tags.add(*tags)
        for data in ingredients:
            ingredient = data.get('ingredient')
            amount = data.get('amount')
            instance.ingredients.add(
                ingredient, through_defaults={"amount": amount})
        return instance
