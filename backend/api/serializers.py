from django.contrib.auth import get_user_model

from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.conf import settings
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers, validators

from api import models
from api.fields import ImageFieldSerialiser


User = get_user_model()


class ProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.following.filter(following_user=obj).exists()
        )


class ProfileCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'password')


class SubscriptionsSerializer(ProfileSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta():
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        limit = self.context.get('recipes_limit', settings.LIMIT_RECIPES)
        recipes = obj.recipes.all()[:int(limit)]
        serializer = RecipeSimpleSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        count = obj.recipes.all().count()
        return count


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserFollowing
        fields = ('user', 'following_user')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=models.UserFollowing.objects.all(),
                fields=['user', 'following_user'],
            )
        ]

    def validate(self, attrs):
        user = attrs.get('user')
        following_user = attrs.get('following_user')
        if user == following_user:
            raise validators.ValidationError(
                'You cannot subscribe to yourself'
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        following_user = instance.following_user
        return SubscriptionsSerializer(following_user,
                                       context=self.context,).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'color', 'slug')

    def to_internal_value(self, data):
        tag = get_object_or_404(models.Tag, id=data)
        return tag


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    measurement_unit = serializers.CharField(read_only=True)

    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(IngredientSerializer):
    amount = serializers.IntegerField()

    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def to_internal_value(self, data):
        ing_id = data.pop('id')
        ingredient = get_object_or_404(models.Ingredient, id=ing_id)
        data['ingredient'] = ingredient
        return data


class RecipeSimpleSerializer(serializers.ModelSerializer):
    image = ImageFieldSerialiser()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(RecipeSimpleSerializer):
    author = ProfileSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time', 'author', 'text',
                  'tags', 'ingredients', 'is_favorited', 'is_in_shopping_cart')

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.annotate(
            amount=F('ingredientamount__amount'))
        serializer = IngredientAmountSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.favorite_list.filter(id=obj.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.shopping_list.filter(id=obj.id).exists()
        )

    def validate_ingredients(self, value):
        serializer = IngredientAmountSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def create(self, validate_data):
        initial_ingred = self.initial_data.get('ingredients')
        ingredients = self.validate_ingredients(initial_ingred)
        tags = validate_data.pop('tags')
        author = self.context.get('request').user
        instance = models.Recipe.objects.create(
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
        instance.text = validated_data.pop('text', instance.text)
        tags = validated_data.get('tags', [])
        instance.tags.set(tags)
        if 'ingredients' in self.initial_data:
            ingredients = self.validate_ingredients(
                self.initial_data.get('ingredients')
            )
            ingr = []
            for data in ingredients:
                ingredient = data.get('ingredient')
                ingr.append(ingredient)
                amount = data.get('amount')
                models.IngredientAmount.objects.update_or_create(
                    ingredient=ingredient,
                    recipe=instance,
                    amount=amount
                )
            instance.ingredients.set(ingr)
        return instance


class FavoriteShoppingCartSerializer(serializers.Serializer):
    def validate(self, attrs):
        recipe = self.context.get('recipe')
        queryset = self.context.get('queryset').all()
        delete = self.context.get('delete')
        if not delete and (recipe in queryset):
            raise validators.ValidationError(
                'The recipe is already in your favorites'
            )
        if delete and (recipe not in queryset):
            raise validators.ValidationError(
                "The recipe isn't yet in your favorites"
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        recipe = self.context.get('recipe')
        return RecipeSimpleSerializer(recipe).data
