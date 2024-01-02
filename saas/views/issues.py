import datetime
import json
import uuid
from hashlib import md5

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from biaodan import issue_form, IssueReplayModelForm, InviteModelForm
from saas.models import Issues, IssuesReply, ProjectUser, IssuesType, ProjectInvite
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe


class Filter(object):
    def __init__(self, filter_name, choices, request):
        self.filter_name = filter_name
        self.choices = choices
        self.request = request

    def __iter__(self):  # 定义一个迭代器方法，让其在前端渲染时循环生成标签
        for item in self.choices:
            key = str(item[0])
            text = item[1]
            ck = ''
            status_list = self.request.GET.getlist(self.filter_name)
            if key in status_list:
                ck = 'checked'
                status_list.remove(key)
            else:
                status_list.append(key)
            qd = self.request.GET.copy()
            qd._mutable = True
            qd.setlist(self.filter_name, status_list)
            if 'page' in qd:
                qd.pop('page')
            url = '{}?{}'.format(self.request.path_info, qd.urlencode())
            html = '<a class="cell" href={url}><input type="checkbox" {checked}/><label>{text}</label></a> '.format(
                checked=ck, text=text, url=url)
            yield mark_safe(html)


class SelectFilter(object):
    def __init__(self, filter_name, choices, request):
        self.filter_name = filter_name
        self.choices = choices
        self.request = request

    def __iter__(self):
        yield mark_safe("<select class='select2' multiple='multiple' style='width:100px;'>")
        for item in self.choices:
            key = str(item[0])
            text = item[1]
            selected = ''

            # 获取url中所有的搜索条件
            status_list = self.request.GET.getlist(self.filter_name)

            # 如果当前循环到的key在已有的搜索条件中，说明此时已经应用过了此搜索条件，在此点击应是消除此搜索条件，故为当前循环到的元素生成的标签应当剔除此元素对应的搜索条件
            if key in self.request.GET.getlist(self.filter_name):
                selected = 'selected'
                status_list.remove(key)

            # 反之亦然
            else:
                status_list.append(key)

            # 构造新的搜索条件： [xx=11,yy=22...]
            qd = self.request.GET.copy()
            qd._mutable = True
            qd.setlist(self.filter_name, status_list)

            # 去除分页条件（分页时选中筛选条件即导致分页效果消失)
            if 'page' in qd:
                qd.pop('page')

            # urlencode生成：'xx=11&yy=22'
            url = '{}?{}'.format(self.request.path_info, qd.urlencode())
            opt = "<option value={url} {selected}>{text}</option>".format(text=text, selected=selected, url=url)
            yield mark_safe(opt)
        yield mark_safe("</select>")


@csrf_exempt
def invite(request, pid):
    """生成邀请码"""
    form = InviteModelForm(data=request.POST)
    if form.is_valid():
        """
        1. 创建随机的邀请码
        2. 该邀请码保存到数据库
        3. 只有项目创建者能够生成邀请码
        """
        if request.saas != request.project.creator:
            form.add_error('period', '只有项目创建者能够生成邀请码')
            return JsonResponse({'status': False, 'errors': form.errors})

        def uid(string):
            data = "{}-{}".format(str(uuid.uuid4()), string)
            return md5(data.encode()).hexdigest()

        randon_code = uid(str(datetime.datetime))
        form.instance.project = request.project
        form.instance.code = randon_code
        form.instance.creator = request.saas
        form.save()

        url = "{scheme}://{host}{path}".format(
            scheme=request.scheme,  # http/https
            host=request.get_host(),  # 主机名+端口
            path=reverse('invite_join', kwargs={'code': randon_code})  # 路径
        )

        return JsonResponse({'status': True, 'data': url})
    return JsonResponse({'status': False, 'errors': form.errors})


def invite_join(request, code):
    """访问邀请码"""
    invite_obj = ProjectInvite.objects.filter(code=code).first()
    if not invite_obj:
        return render(request, 'saas/invite_join.html', {'errors': '邀请码不存在'})

    # 已经在项目里？
    exist = ProjectUser.objects.filter(project=invite_obj.project, user=request.saas).exists()
    if invite_obj.creator == request.saas or exist:
        return render(request, 'saas/invite_join.html', {'errors': '您无需再加入项目'})

    # 邀请码过期？
    limit = invite_obj.create_datetime + datetime.timedelta(minutes=invite_obj.period)
    current = datetime.datetime.now(tz=invite_obj.create_datetime.tzinfo)
    if current >= limit:
        return render(request, 'saas/invite_join.html', {'errors': '邀请码已过期'})

    # 数量限制？
    if invite_obj.count:
        if invite_obj.use_count >= invite_obj.count:
            return render(request, 'saas/invite_join.html', {'errors': '邀请人数已达上限'})
        invite_obj.use_count += 1
        invite_obj.save()

    ProjectUser.objects.create(user=request.saas, project=invite_obj.project)
    return render(request, 'saas/invite_join.html', {'project_id': invite_obj.project.id})


def show_issues(request, pid):
    if request.method == 'GET':
        # 筛选功能
        allow_filter_name = ['issue_type', 'status', 'priority', 'issues_type', 'assign', 'attention']
        total_condition = {}
        for name in allow_filter_name:
            if not request.GET.getlist(name):
                continue
            total_condition['{}__in'.format(name)] = request.GET.getlist(name)  # [number1,number2]
        """
        total_condition = {
            'status__in':[1,2],
            'priority__in':[3,4,5]        
        }
        """

        totaluser_list = [(request.project.creator.id, request.project.creator.username), ]
        totaluser_list.extend(ProjectUser.objects.filter(project_id=pid).values_list('user_id', 'user__username'))

        form = issue_form(request)
        invite_form = InviteModelForm()
        obj_list = Issues.objects.filter(project=request.project).filter(
            **total_condition).all()  # 这里是Filter条件传入字典以搜索的方法
        return render(request, 'saas/show_issues.html',
                      {'form': form, 'invite_form': invite_form, 'object_list': obj_list,
                       'status_filter': Filter('status', Issues.status_choices,
                                               request),
                       'priority_filter': Filter('priority', Issues.priority_choices,
                                                 request),
                       'mode_filter': Filter('mode', Issues.mode_choices, request),
                       'issues_type_filter': Filter('issues_type',
                                                    IssuesType.objects.filter(
                                                        project_id=pid).values_list(
                                                        'id', 'title'), request),
                       'assign_filter': SelectFilter('assign', totaluser_list, request),
                       'attention_filter': SelectFilter('attention', totaluser_list, request), })


@csrf_exempt
def add_issues(request, pid):
    form = issue_form(request, data=request.POST)
    if form.is_valid():
        form.instance.creator = request.saas
        form.instance.project = request.project
        form.save()
        return JsonResponse({'status': True})
    print(form.errors)
    return JsonResponse({'status': False, 'errors': form.errors})


@csrf_exempt
def detail_issues(request, pid, iid):
    def create_record_reply_to_qianduan(change_record):
        # 在数据库生成一条评论（更新记录）
        instance = IssuesReply.objects.create(
            reply_type=1,
            issues=issue_obj,
            content=change_record,
            creator=request.saas
        )
        # 评论传回前端
        data = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': instance.reply_id,
        }
        return data

    if request.method == 'GET':
        qs = Issues.objects.filter(id=iid, project_id=pid).first()
        issue_id = qs.id
        form = issue_form(request, instance=qs)
        return render(request, 'saas/detail_issues.html', {'form': form, 'issue_id': issue_id})

    post_dict = json.loads(request.body.decode('utf-8'))
    print(post_dict)
    # 获取当前操作的问题（对象）
    issue_obj = Issues.objects.filter(project_id=pid, id=iid).first()

    # 1.数据库字段更新
    name = post_dict['name']
    value = post_dict['value']
    # 获取当前表结构ORM字段,以判断该字段能否为空
    field_obj = Issues._meta.get_field(name)
    # a. 文本字段
    if name in ['subject', 'desc', 'start_date', 'end_date']:
        if not value:
            if field_obj.null:
                setattr(issue_obj, name, None)
                issue_obj.save()
                change_record = "{}更新为空".format(field_obj.verbose_name)
            else:
                return JsonResponse({'status': False, 'errors': {name: '该字段不可为空'}})
        else:
            setattr(issue_obj, name, value)
            issue_obj.save()
            change_record = "{}更新为{}".format(field_obj.verbose_name, value)

            # 在数据库生成一条评论（更新记录）
            instance = IssuesReply.objects.create(
                reply_type=1,
                issues=issue_obj,
                content=change_record,
                creator=request.saas
            )

            # 更新记录传回前端
            data = {
                'id': instance.id,
                'reply_type_text': instance.get_reply_type_display(),
                'content': instance.content,
                'creator': instance.creator.username,
                'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
                'parent_id': instance.reply_id,
            }
            return JsonResponse({'status': True, 'data': data})
    # b. FK字段
    if name in ['issues_type', 'module', 'parent', 'assign']:
        if not value:  # 用户输入为空
            if field_obj.null:
                setattr(issue_obj, name, None)
                issue_obj.save()
                change_record = "{}被更新为空".format(field_obj.verbose_name)
            else:
                return JsonResponse({'status': False, 'errors': {name: '该字段不可为空'}})
        else:  # 用户输入不为空
            if name == 'assign':  # 判断指派者是否为当前项目创建者或者参与者
                if value == request.project.creator_id:  # 是创建者
                    instance = request.project.creator  # 把创建者对象赋值给instance，用于后续保存入数据库（外键需要对象进行入库）
                else:
                    project_user_object = ProjectUser.objects.filter(project_id=pid, user_id=value).first()
                    if not project_user_object:  # 啥也不是
                        instance = None
                    else:  # 是参与者
                        instance = project_user_object.user
                if not instance:
                    return JsonResponse({'status': False, 'errors': {name: '该用户不存在'}})

                # 保存入库并返回前端
                setattr(issue_obj, name, instance)
                issue_obj.save()
                change_record = "{}更新为{}".format(field_obj.verbose_name, str(instance))
                return JsonResponse({'status': True, 'data': create_record_reply_to_qianduan(change_record)})

            else:
                instance = field_obj.remote_field.model.objects.filter(id=value, project_id=pid).first()
                if not instance:
                    return JsonResponse({'status': False, 'errors': {name: '该值不存在'}})

                # 保存入库并返回前端
                setattr(issue_obj, name, instance)
                issue_obj.save()
                change_record = "{}更新为{}".format(field_obj.verbose_name, str(instance))
                return JsonResponse({'status': True, 'data': create_record_reply_to_qianduan(change_record)})
    # c. choices字段
    if name in ['priority', 'status', 'mode']:
        selected_text = None
        for key, text in field_obj.choices:
            if key == value:
                selected_text = text
        if not selected_text:
            return JsonResponse({'status': False, 'errors': {name: '您选择的值不存在'}})

        setattr(issue_obj, name, selected_text)
        issue_obj.save()
        change_record = "{}更新为{}".format(field_obj.verbose_name, str(selected_text))
        return JsonResponse({'status': True, 'data': create_record_reply_to_qianduan(change_record)})
    # d. m2m字段
    if name == 'attention':
        if not isinstance(value, list):  # 前端传过来的数据不是列表格式
            return JsonResponse({'status': False, 'errors': {name: '数据格式错误'}})
        if not value:  # 前端传过来的值为空，代表该问题没有关注者
            issue_obj.attention.set([])  # 把m2m的第三张表(attention)，与当前issue_obj关联的行都清空
            issue_obj.save()
            change_record = "{}更新为空".format(field_obj.verbose_name)
        else:
            total_user_dict = {str(request.project.creator.id): request.project.creator.username}
            project_user_obj = ProjectUser.objects.filter(project_id=pid).all()
            for item in project_user_obj:
                total_user_dict[str(item.user_id)] = item.user.username
            username_list = []
            for user_id in value:
                if not total_user_dict.get(str(user_id)):  # 在该项目所有参与者+创建者中都找不到现在传入的id（dict.get()方法)
                    return JsonResponse({'status': False, 'errors': {name: '用户不存在，请重试'}})
                username_list.append(total_user_dict.get(str(user_id)))  # 把匹配出的用户名放入列表准备传回前端

            # 更新数据库并返回数据给前端
            issue_obj.attention.set(value)  # 更新m2m的第三张表(attention)，此处用set方法并传入字典，django会将原本数据更新为新传入的数据
            issue_obj.save()
            change_record = "{}被更新为{}".format(field_obj.verbose_name,
                                                  ','.join(username_list))  # 字符串操作的join方法，将一个可迭代对象变成一个字符串，元素之间以指定的符号分割
        return JsonResponse({'status': True, 'data': create_record_reply_to_qianduan(change_record)})
    return JsonResponse({'status': False, 'errors': {name: '非法操作'}})


@csrf_exempt
def detail_reply_issues(request, pid, iid):
    if request.method == 'GET':
        # 展示
        qs = IssuesReply.objects.filter(issues_id=iid, issues__project=request.project).all()
        print(qs)
        if qs:
            data_list = []
            for row in qs:
                data = {
                    'id': row.id,
                    'reply_type_text': row.get_reply_type_display(),
                    'content': row.content,
                    'creator': row.creator.username,
                    'datetime': row.create_datetime.strftime("%Y-%m-%d %H:%M"),
                    'parent_id': row.reply_id,
                }
                data_list.append(data)
            return JsonResponse({'status': True, 'data': data_list})
        return JsonResponse({'status': False, 'error': 'no_comment'})

    # 处理提交过来的reply
    form = IssueReplayModelForm(data=request.POST)

    if form.is_valid():
        form.instance.issues_id = iid
        form.instance.reply_type = 2
        form.instance.creator = request.saas
        instance = form.save()
        info = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status': True, 'data': info})
    return JsonResponse({'status': False, 'errors': form.errors})
