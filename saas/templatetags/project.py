from django.template import Library

from saas.models import Project, ProjectUser

register = Library()


@register.inclusion_tag('tags/project_list.html')
def all_project(request):
    create = Project.objects.filter(creator=request.saas).all()
    join = ProjectUser.objects.filter(user=request.saas).all()
    return {'create': create, 'join': join}

@register.simple_tag
def string_just(num):
    if num <100:
        num = str(num).rjust(5 ,'0')
    return "#{}".format(num)