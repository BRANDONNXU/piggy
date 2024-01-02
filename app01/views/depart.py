from django.shortcuts import render, redirect
from app01.models import Department
from biaodan import Edit_department_form


def show_department(request):
    data_list = Department.objects.all()
    return render(request, 'app01/show_department.html', {'data_list': data_list})


def edit_department(request, did):
    row_obj = Department.objects.filter(id=did).first()
    depart_id = row_obj.id
    if request.method == "GET":
        form = Edit_department_form(instance=row_obj)
        return render(request, 'app01/edit_department.html', {"form": form, "depart_id": depart_id}, )

    form = Edit_department_form(data=request.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return redirect('/erp/depart_list/')
    return render(request, 'app01/edit_department.html', {"form": form})


def delete_department(request, did):
    delete_depart_name = Department.objects.filter(id=did).delete()
    return redirect('/erp/depart_list/')


def create_department(request):
    if request.method == "GET":
        return render(request, 'app01/create_department.html')
    create_depart_name = request.POST.get("create_depart_name")
    Department.objects.create(depart=create_depart_name)
    return redirect('/erp/depart_list/')
