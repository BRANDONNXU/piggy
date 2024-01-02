"""
URL configuration for django_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

import app01
import saas
from saas.views import account, project_manage, project_setup, issues
from app01.views import admin, depart, users, order, statistic, test_script

urlpatterns = [
    path('test_script/', app01.views.test_script.test),
    path('erp/user_list/', app01.views.users.show_users),
    path('erp/user_list/create_user/', app01.views.users.create_user),
    path('erp/user_list/<int:uid>/delete_user/', app01.views.users.delete_user),
    path('erp/user_list/<int:uid>/edit_user/', app01.views.users.edit_user),

    path('erp/admin_list/', app01.views.admin.show_admin),
    path('erp/admin_list/create_admin/', app01.views.admin.create_admin),
    path('erp/admin_list/<int:uid>/resetpwd_admin/', app01.views.admin.resetpwd_admin),
    path('homepage/', app01.views.admin.homepage),
    path('', app01.views.admin.homepage),

    path('erp/depart_list/', app01.views.depart.show_department),
    path('erp/depart_list/<int:did>/edit_depart/', app01.views.depart.edit_department),
    path('erp/depart_list/<int:did>/delete_depart/', app01.views.depart.delete_department),
    path('erp/depart_list/create_depart/', app01.views.depart.create_department),

    path('erp/order_list/', app01.views.order.show_order),
    path('erp/order_list/add', app01.views.order.add_order),
    path('erp/order_list/edit', app01.views.order.edit_order),

    path('erp/login/', app01.views.admin.login),
    path('code/', app01.views.admin.generate_code),
    path('erp/register/', app01.views.admin.register),
    path('erp/statistic/', app01.views.statistic.show_statistic),

    path('saas/login/', saas.views.account.saas_login),
    path('saas/register/', saas.views.account.saas_register),
    path('saas/project_list/', saas.views.account.show_project_list),
    path('saas/project_list/add_star/', saas.views.account.add_star),
    path('saas/project_list/remove_star/', saas.views.account.remove_star),

    path('saas/manage/<int:pid>/dashboard/', saas.views.project_manage.dashboard,name='dashboard'),
    path('saas/manage/<int:pid>/setup/', saas.views.project_setup.show_setup),
    path('saas/manage/<int:pid>/setup/delete_project/', saas.views.project_setup.delete_project, name="delete_project"),

    path('saas/manage/<int:pid>/wiki/', saas.views.project_manage.wiki, name='wiki'),
    path('saas/manage/<int:pid>/wiki/add/', saas.views.project_manage.add_wiki),
    path('saas/manage/<int:pid>/wiki/catalog/', saas.views.project_manage.catalog, name='wiki_catalog'),

    path('saas/manage/<int:pid>/file/', saas.views.project_manage.file, name='file'),
    path('saas/manage/<int:pid>/cos_credential/', saas.views.project_manage.cos_credential, name='cos_credential'),
    path('saas/manage/<int:pid>/file/check_file_before_upload/', saas.views.project_manage.check_file_before_upload,
         name='check_file_before_upload'),
    path('saas/manage/<int:pid>/file/check_file_after_upload/', saas.views.project_manage.check_file_after_upload,
         name='check_file_after_upload'),
    path('saas/manage/<int:pid>/file/file_download/<int:fid>/', saas.views.project_manage.download_file,name='file_download'),
    path('saas/manage/<int:pid>/file/file_delete/', saas.views.project_manage.delete_file,name='file_delete'),

    path('saas/manage/<int:pid>/issues/', saas.views.issues.show_issues, name='show_issues'),
    path('saas/manage/<int:pid>/issues/add/', saas.views.issues.add_issues, name='add_issues'),
    path('saas/manage/<int:pid>/issues/invite/', saas.views.issues.invite, name='invite'),
    path('saas/manage/<int:pid>/issues/detail/<int:iid>/', saas.views.issues.detail_issues,name='detail_issues'),
    path('saas/manage/<int:pid>/issues/detail_reply/<int:iid>/', saas.views.issues.detail_reply_issues,name='detail_reply_issues'),
    path('saas/invite_join/<str:code>/', saas.views.issues.invite_join,name='invite_join'),

]
