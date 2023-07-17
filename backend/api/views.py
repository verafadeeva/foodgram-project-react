from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import models, serializers

User = get_user_model()


class ProfileViewSet(UserViewSet):
    queryset = User.objects.all().prefetch_related(
        'following').prefetch_related('followers')
    allowed_methods = ('post', 'get')

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.ProfileCreateSerializer
        elif self.action in ('subscriptions', 'subscribe'):
            return serializers.SubscriptionsSerializer
        elif self.action in ('list', 'retrieve'):
            return serializers.ProfileSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(followers__user=user)
        # page = self.paginate_queryset(recent_users)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        user = request.user
        id = self.kwargs.get('id')
        following_user = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if user == following_user:
                data = {'errors': 'You cannot subscribe to yourself'}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            instance, stat = models.UserFollowing.objects.get_or_create(
                user=user,
                following_user=following_user
            )
            if stat is False:
                data = {'errors': 'You are already subscribed'}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(following_user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                instance = models.UserFollowing.objects.get(
                    user=user,
                    following_user=following_user
                )
                instance.delete()
            except models.UserFollowing.DoesNotExist:
                data = {'errors': 'You are not subscribed yet'}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class RecipeViewSet(viewsets.ModelViewSet):
    # queryset = models.Recipe.objects.all().select_related(
    #     'author').prefetch_related('tags', 'ingredients')
    queryset = models.Recipe.objects.all().select_related(
        'author').prefetch_related(
            'tags',
            Prefetch('ingredients', queryset=models.Ingredient.objects.annotate())
        )
    serializer_class = serializers.RecipeSerializer

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return serializers.RecipeSimpleSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        data = super().get_serializer_context()
        data['queryset'] = self.queryset
        return data


    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(models.Recipe, id=pk)

        if request.method == 'POST':
            if recipe in user.favorite_list.all():
                data = {'errors': 'The recipe is already in your favorites'}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            user.favorite_list.add(recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if recipe not in user.favorite_list.all():
                data = {'errors': "The recipe isn't yet in your favorites"}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            user.favorite_list.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(models.Recipe, id=pk)

        if request.method == 'POST':
            if recipe in user.shopping_list.all():
                data = {'errors': 'The recipe is in your shopping cart'}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            user.shopping_list.add(recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if recipe not in user.shopping_list.all():
                data = {'errors': "The recipe isn't yet in your shopping cart"}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            user.shopping_list.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list = user.shopping_list.all()

