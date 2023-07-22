from django.http import HttpResponse


def make_text(queryset):
    output = []
    output.append('Your shopping list')
    output.append('\n')
    for i, obj in enumerate(queryset):
        line = f'{i+1}. {obj.name}: {obj.total_amount} {obj.measurement_unit}'
        output.append(line)
    return '\n'.join(output)


def create_txt(queryset):
    text = make_text(queryset)
    response = HttpResponse(
        text,
        'Content-Type: application/pdf',
        headers={
            "Content-Disposition": 'attachment; filename="shopping_list.txt"'
                }
            )
    return response
