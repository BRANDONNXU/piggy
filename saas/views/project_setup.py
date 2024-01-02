from django.shortcuts import render, redirect

from saas.models import Project


def show_setup(request, pid):
    return render(request, 'saas/setup.html')


def delete_project(request, pid):
    """删除项目"""
    if request.method == 'GET':
        return render(request, 'saas/setup.html')
    project_name = request.POST.get('project_to_delete')
    if not project_name or project_name != request.project.name:
        return render(request, 'saas/setup.html', {'errors': '项目名输入错误'})

    if request.project.creator != request.saas:
        return render(request, 'saas/setup.html', {'errors': '您不是该项目的创建者，您无权删除该项目'})

    # 删除桶
    #  删除文件、文件碎片
    # 删除项目
    from saas.tools.tencent_cos import delete_bucket
    delete_bucket(request.project.bucket, request.project.bucket_region)
    Project.objects.filter(id=request.project.id).delete()
    return redirect('/saas/project_list/')
