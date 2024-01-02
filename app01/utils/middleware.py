import sys

from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from saas.models import Users, Project, ProjectUser


# 登录中间件
class LoginMiddleWare(MiddlewareMixin):
    def process_request(self, request):
        if request.path_info in ["/erp/login/", "/code/", "/erp/register/", "/saas/register/", "/saas/login/",
                                 "/homepage/"]:
            return
        if request.path_info.startswith('/erp/'):
            exist = request.session.get('erp_info_dict')
            if not exist:
                return redirect('/erp/login/')
        if request.path_info.startswith('/saas/'):
            exist = request.session.get('saas_info_dict')
            if not exist:
                return redirect('/saas/login/')

        return


# 储存用户信息到request中间件
class AuthMiddleWare(MiddlewareMixin):

    def process_request(self, request):
        if request.path_info in ["/erp/login/", "/code/", "/erp/register/", "/saas/register/", "/saas/login/",
                                 "/homepage/", "/test_script/"]:
            return

        if request.path_info.startswith('/saas/'):
            key = request.session['saas_info_dict']['id']
            user_object = Users.objects.filter(id=key).first()
            if user_object:
                request.saas = user_object  # 把当前登录的用户对象封装到request中，以便于在视图函数中访问
                return
            return
        return

    def process_view(self, request, view, arg, kwargs):
        if not request.path_info.startswith('/saas/manage/'):
            return

        project_id = kwargs.get('pid')

        project_obj = Project.objects.filter(creator=request.saas, id=project_id).first()
        if project_obj:
            # 是我创建的项目
            request.project = project_obj
            return

        project_user_obj = ProjectUser.objects.filter(user=request.saas, id=project_id).first()
        if project_user_obj:
            # 是我参与的项目
            request.project = project_user_obj.project
            return

        return redirect('/saas/project_list/')
