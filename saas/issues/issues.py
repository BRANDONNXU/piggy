from django.template import Library

register = Library()

@register.simple_tag
def string_just(num):
    if num <100:
        num = str(num).rjust(5 ,'0')
    return "#{}".format(num)
