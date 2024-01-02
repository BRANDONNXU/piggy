from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe

from biaodan import saas_register_form, saas_create_project_form
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from saas.models import Users, Transaction, PricePolicy, Project, ProjectUser, IssuesType
import uuid, datetime

from saas.tools import tencent_cos
import time


def saas_login(request):
    if request.method == 'GET':
        return render(request, 'saas/saas_login.html')
    input_check_code = request.POST.get('check_code')

    # 首先进行验证码校验
    input_check_code = request.POST.get('check_code')
    input_email_or_mobile_phone = request.POST.get('username')
    input_password = request.POST.get('password')
    if input_check_code.upper() != request.session.get('check_code'):
        check_code_error = '<div style="color:red;font-size:10px;margin-bottom: 10px;margin_top:-10px">验证码错误</div>'
        check_code_error = mark_safe(check_code_error)
        return render(request, 'saas/saas_login.html',
                      {"check_code_error": check_code_error, 'input_email_or_mobile_phone': input_email_or_mobile_phone,
                       'input_password': input_password})

    # 用户名密码校验

    exist_1 = Users.objects.filter(email=input_email_or_mobile_phone, password=input_password).first()
    exist_2 = Users.objects.filter(mobile_phone=input_email_or_mobile_phone, password=input_password).first()
    if not exist_1 and not exist_2:
        check_code_error = '<div style="color:red;font-size:10px;margin-bottom: 10px;margin_top:-10px">用户名或密码错误</div>'
        check_code_error = mark_safe(check_code_error)
        return render(request, 'saas/saas_login.html',
                      {"check_code_error": check_code_error, 'input_email_or_mobile_phone': input_email_or_mobile_phone,
                       'input_password': input_password})

    # 登陆成功，记录cookie
    if True:
        if exist_1:
            id = exist_1.id
            request.session['saas_info_dict'] = {'id': id}
            print(request.session['saas_info_dict']['id'])
            print(request.session['saas_info_dict'])
            request.session.set_expiry(60 * 60 * 24)
            return redirect('/saas/project_list')
        if exist_2:
            id = exist_2.id
            request.session['saas_info_dict'] = {'id': id}
            print(request.session['saas_info_dict']['id'])
            print(request.session['saas_info_dict'])
            request.session.set_expiry(60 * 60 * 24)
            return redirect('/saas/project_list')

    # if exist_1:
    #     print(1)
    #     request.session['saas_info_dict'] = {'user': exist_1}
    #     return redirect('/saas/project_list')
    # if exist_2:
    #     print(2)
    #     request.session['saas_info_dict'] = {'user': exist_2}
    #     print(3)
    #     return redirect('/saas/project_list')

    # 记录cookie出错
    check_code_error = '<div style="color:red;font-size:10px;margin-bottom: 10px;margin_top:-10px">登陆出错，请重试</div>'
    check_code_error = mark_safe(check_code_error)
    return render(request, 'saas/saas_login.html',
                  {"check_code_error": check_code_error, 'input_email_or_mobile_phone': input_email_or_mobile_phone,
                   'input_password': input_password})


@csrf_exempt
def saas_register(request):
    if request.method == 'GET':
        form = saas_register_form()
        return render(request, 'saas/saas_register.html', {'form': form})

    input_check_code = request.POST.get('check_code')
    if input_check_code.upper() != request.session.get('check_code'):
        return JsonResponse({'status': False, 'errors': {'check_code': ['验证码输入错误']}})
    form = saas_register_form(data=request.POST)
    print(request.POST)
    if form.is_valid():
        instance = form.save()
        price_policy = PricePolicy.objects.filter().first()
        Transaction.objects.create(status=1, order=str(uuid.uuid4()), user=instance, price_policy=price_policy, count=0,
                                   price=0,
                                   start_datetime=datetime.datetime.now(), create_datetime=datetime.datetime.now())
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'errors': form.errors})


@csrf_exempt
def show_project_list(request):
    if request.method == 'GET':
        form = saas_create_project_form(request)
        project_list = {'star': [], 'my_create': [], 'my_join': []}
        my_create = Project.objects.filter(creator=request.saas).all()
        for item in my_create:
            if item.star:
                project_list['star'].append(item)
            else:
                project_list['my_create'].append(item)
        my_join = ProjectUser.objects.filter(user=request.saas).all()
        for item in my_join:
            if item.star:
                project_list['star'].append(item.project)
            else:
                project_list['my_join'].append(item.project)
        print(project_list)

        return render(request, 'saas/saas_homepage.html', {'form': form, 'project_list': project_list})

    # 创建项目
    form = saas_create_project_form(request, data=request.POST)
    print(request.POST)
    print(request.session['saas_info_dict']['id'])
    if form.is_valid():
        bucket_name = '{}-{}-1320839699'.format(request.saas.mobile_phone, int(time.time() * 1000))
        print(bucket_name)
        # 为项目创建存储桶
        try:

            tencent_cos.create_bucket(region='ap-guangzhou', Bucket=bucket_name)

            form.instance.bucket = bucket_name

            form.instance.bucket_region = 'ap-guangzhou'

        except:
            return JsonResponse({'status': False, 'erros': '1'})

        # 把项目保存到数据库
        form.instance.creator = request.saas
        instance = form.save()

        # 为项目初始化问题类型
        issue_type_object_list = []
        for item in IssuesType.DEFAULT_ISSUES_TYPE:
            issue_type_object_list.append(IssuesType(project=instance, title=item))
        IssuesType.objects.bulk_create(issue_type_object_list)
        return JsonResponse({'status': True})

    return JsonResponse({'status': False, 'errors': form.errors})


@csrf_exempt
def add_star(request):
    project_id = request.POST.get('id')
    project_type = request.POST.get('type')
    if project_type == 'create':
        Project.objects.filter(id=project_id).update(star=True)
        return JsonResponse({'Status': True})
    if project_type == 'join':
        ProjectUser.objects.filter(project=Project.objects.filter(id=project_id).first()).update(star=True)
        return JsonResponse({'Status': True})
    return JsonResponse({'Status': False})


@csrf_exempt
def remove_star(request):
    # 先区分此星标项目是“我创建的”or“我参与的”
    project_id = request.POST.get('id')
    project_type = request.POST.get('type')
    if project_type == 'create':
        Project.objects.filter(id=project_id).update(star=False)
        return JsonResponse({'Status': True})
    if project_type == 'join':
        ProjectUser.objects.filter(project=Project.objects.filter(id=project_id).first()).update(star=False)
        return JsonResponse({'Status': True})
    return JsonResponse({'Status': False})
