from rest_framework import filters


class RecipeFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        query = request.query_params
        tags = query.getlist('tags')
        author = query.get('author')
        if tags:
            if len(tags) == 1:
                queryset = queryset.filter(tags__slug=tags[0])
            elif len(tags) == 2:
                queryset = (queryset.filter(tags__slug=tags[0])
                            | queryset.filter(tags__slug=tags[1]).exclude(
                                tags__slug=tags[0])
                            )
        elif author is not None:
            queryset = queryset.filter(author__id=int(author))
        if not user.is_anonymous:
            is_favorited = query.get('is_favorited')
            is_in_shopping_cart = query.get('is_in_shopping_cart')
            if is_favorited == '1':
                queryset = user.favorite_list.all()
            elif is_in_shopping_cart == '1':
                queryset = user.shopping_list.all()
        return queryset
