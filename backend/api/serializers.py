import base64
from time import time

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
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
        if user.is_anonymous:
            return False
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


class SubscriptionsSerializer(ProfileSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipes'] = serializers.SerializerMethodField()
        self.fields['recipes_count'] = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        limit = self.context.get('recipes_limit')
        recipes = obj.recipes.all()[:int(limit)]
        serializer = RecipeSimpleSerializer(recipes, many=True)
        return serializer.data

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
        self.fields['amount'] = serializers.IntegerField()

    # def get_amount(self, obj):
    #     recipe_id = self.context.get('view').kwargs.get('pk')
    #     if recipe_id is None:
    #         amount = obj.ingredientamount_set.all()[0].amount
    #     else:
    #         amount = obj.ingredientamount_set.get(recipe__id=recipe_id).amount
    #     return amount

    def to_internal_value(self, data):
        ing_id = data.pop('id')
        ingredient = get_object_or_404(models.Ingredient, id=ing_id)
        data['ingredient'] = ingredient
        return data


class ImageFieldSerialiser(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f'{int(time())}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
        return super().to_internal_value(data)


class RecipeSimpleSerializer(serializers.ModelSerializer):
    image = ImageFieldSerialiser()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(RecipeSimpleSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['author'] = ProfileSerializer(read_only=True)
        self.fields['tags'] = TagSerializer(many=True)
        # self.fields['ingredients'] = IngredientAmountSerializer(many=True)
        self.fields['ingredients'] = serializers.SerializerMethodField()
        self.fields['is_favorited'] = serializers.SerializerMethodField(
            read_only=True)
        self.fields['is_in_shopping_cart'] = serializers.SerializerMethodField(
            read_only=True)

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.annotate(
            amount=F('ingredientamount__amount'))
        serializer = IngredientAmountSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        favorited_for = obj.favorited_for.all()
        return True if user in favorited_for else False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        added_to_cart = obj.added_to_cart.all()
        return True if user in added_to_cart else False

    def validate_ingredients(self, data):
        validated_data = []
        for d in data:
            serializer = IngredientAmountSerializer(data=d)
            if not serializer.is_valid():
                raise serializers.ValidationError('Ingredients field is required')
            validated_data.append(serializer.validated_data)
        return validated_data

    def create(self, validate_data):
        initial = self.initial_data.get('ingredients')
        ingredients = self.validate_ingredients(initial)
        author = self.context.get('request').user
        tags = validate_data.pop('tags')
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

    def update(self, instance, validated_data):
        instance.name = validated_data.pop('name', instance.name)
        instance.image = validated_data.pop('name', instance.image)
        instance.cooking_time = validated_data.pop('name',
                                                   instance.cooking_time)
        tags = validated_data.pop('tags')
        for tag in tags:
            if tag in instance.tags.all():
                instance.tags.remove(tag)
            else:
                instance.tags.add(tag)
        ingredients = validated_data.pop('ingredients')
        for data in ingredients:
            ingredient = data.get('ingredient')
            amount = data.get('amount')
            if ingredient in instance.ingredients.all():
                instance.ingredients.remove(
                    ingredient, through_defaults={"amount": amount})
            else:
                instance.ingredients.add(
                    ingredient, through_defaults={"amount": amount})
        return instance
