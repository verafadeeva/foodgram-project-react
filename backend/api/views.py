from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters import rest_framework
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import models, serializers
from api.permissions import IsAuthorOrReadOnly
from api.filters import RecipeFilter
from api.utils import create_txt

User = get_user_model()


class ProfileViewSet(UserViewSet):
    queryset = User.objects.all().prefetch_related(
        'following').prefetch_related('followers').order_by('id')
    allowed_methods = ('post', 'get')
    permission_classes = settings.PERMISSIONS.user

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = settings.PERMISSIONS.retrieve
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.ProfileCreateSerializer
        elif self.action == 'subscriptions':
            return serializers.SubscriptionsSerializer
        elif self.action == 'subscribe':
            return serializers.SubscribeSerializer
        elif self.action in ('list', 'retrieve'):
            return serializers.ProfileSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        data = super().get_serializer_context()
        recipes_limit = self.request.query_params.get(
            "recipes_limit",
            settings.LIMIT_RECIPES,
        )
        data['recipes_limit'] = recipes_limit
        return data

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        user = self.get_instance()
        queryset = User.objects.filter(followers__user=user).order_by('id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        user = self.get_instance()
        following_user = get_object_or_404(User, id=id)
        if request.method == 'DELETE':
            instance = models.UserFollowing.objects.filter(
                user=user,
                following_user=following_user,
            )
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            data = {'errors': 'You are not subscribed yet'}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(
            data={'user': user.id,
                  'following_user': following_user.id,
                  }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all().select_related(
        'author').prefetch_related('tags', 'ingredients')
    serializer_class = serializers.RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (rest_framework.DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return serializers.FavoriteShoppingCartSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(models.Recipe, pk=pk)
        if request.method == 'DELETE':
            serializer = self.get_serializer(
                data={'pk': pk},
                context={'request': request,
                         'recipe': recipe,
                         'queryset': user.favorite_list,
                         'delete': True},
            )
            serializer.is_valid(raise_exception=True)
            user.favorite_list.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(
            data={'pk': pk},
            context={'request': request,
                     'recipe': recipe,
                     'queryset': user.favorite_list,
                     'delete': False},
        )
        serializer.is_valid(raise_exception=True)
        user.favorite_list.add(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(models.Recipe, pk=pk)
        if request.method == 'DELETE':
            serializer = self.get_serializer(
                data={'pk': pk},
                context={'request': request,
                         'recipe': recipe,
                         'queryset': user.shopping_list,
                         'delete': True},
            )
            serializer.is_valid(raise_exception=True)
            user.shopping_list.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(
            data={'pk': pk},
            context={'request': request,
                     'recipe': recipe,
                     'queryset': user.shopping_list,
                     'delete': False},
        )
        serializer.is_valid(raise_exception=True)
        user.shopping_list.add(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_list = user.shopping_list.all()
        queryset = models.Ingredient.objects.filter(
            ingredientamount__recipe__in=shopping_list
        ).annotate(total_amount=Sum('ingredientamount__amount'))
        return create_txt(queryset)
