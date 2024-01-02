from saas.models import Project, FileBank, IssuesType
from django.http import JsonResponse, HttpResponse


def test(request):
    parent_obj = FileBank.objects.filter(id=37, file_type=2).first()
    temp_parent_obj = parent_obj
    nav_obj = []

    print(id(parent_obj))
    print(id(temp_parent_obj))
    while temp_parent_obj:
        nav_obj.insert(0, temp_parent_obj)
        temp_parent_obj = temp_parent_obj.parent

    print(id(parent_obj))
    print(id(temp_parent_obj))
    print(parent_obj)
    print(temp_parent_obj)
    print(nav_obj)
    return HttpResponse('11')
