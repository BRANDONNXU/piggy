from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from biaodan import wiki_form, FileFolderModelForm, FileSaveModelForm
from django_project import settings
from saas.models import Wiki, FileBank, Project
import json


def dashboard(request, pid):
    return render(request, 'saas/dashboard.html')


def wiki(request, pid):
    if request.GET.get('wid'):
        wiki_obj = Wiki.objects.filter(id=request.GET.get('wid')).first()
        return render(request, 'saas/wiki.html', {'wiki_obj': wiki_obj})
    return render(request, 'saas/wiki.html')


def catalog(request, pid):
    obj_list = Wiki.objects.filter(project=request.project).all().order_by('depth', 'id').values('id', 'title',
                                                                                                 'parent_id')
    print(list(obj_list))
    return JsonResponse(list(obj_list), safe=False)


def add_wiki(request, pid):
    if request.method == "GET":
        form = wiki_form(request)
        return render(request, 'saas/add_wiki.html', {'form': form})

    form = wiki_form(request, data=request.POST)
    if form.is_valid():
        form.instance.project = request.project
        if not form.instance.parent:
            form.instance.depth = 1
        else:
            form.instance.depth = form.instance.parent.depth + 1
        form.save()
        # 通过pid反向生成url
        url = reverse('wiki', args=[pid])
        return redirect(url)


def file(request, pid):
    # 先默认无父目录，若有父目录则添加，若无则认定为根目录
    parent_obj = None
    folder = request.GET.get('folder', '')
    if folder:
        parent_obj = FileBank.objects.filter(id=int(folder), file_type=2, project=request.project).first()

    if request.method == 'GET':
        # 导航条列表
        nav_obj = []

        # 拷贝一份临时父对象，用于查找其所有父对象，而不改变parent_obj（后需要向前端传参）
        temp_parent_obj = parent_obj
        while temp_parent_obj:
            nav_obj.insert(0, temp_parent_obj)
            temp_parent_obj = temp_parent_obj.parent

        # 查询当前页面所有需要展示的file_obj
        file_obj = FileBank.objects.filter(project=request.project, parent=parent_obj).all().order_by('-file_type')
        if parent_obj == None:
            parent_obj = 'null'
        form = FileFolderModelForm(request, parent_obj)
        return render(request, 'saas/show_file.html', {'form': form, 'file_obj': file_obj, 'nav_obj': nav_obj,
                                                       'parent_obj': parent_obj})  # 此处parent_obj用于前端直传COS时，向后端返回数据存入数据库时使用

    # 检查POST请求中有无携带fid
    fid = request.POST.get('fid')

    # 编辑
    if fid:
        row_obj = FileBank.objects.filter(id=fid).first()
        form = FileFolderModelForm(request, parent_obj, data=request.POST, instance=row_obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': True})
        return JsonResponse({'status': False, 'errors': form.errors})

    # 新增
    form = FileFolderModelForm(request, parent_obj, data=request.POST)
    if form.is_valid():
        # 判断其是否为根目录文件夹，若是，则设定其父文件字段为空
        form.instance.parent = parent_obj
        form.instance.project = request.project
        form.instance.file_type = 2
        form.instance.update_user = request.saas
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'errors': form.errors})


def cos_credential(request, pid):
    from sts.sts import Sts
    config = {
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 500,
        'secret_id': settings.TENCENT_COS_ID,
        # 固定密钥
        'secret_key': settings.TENCENT_COS_KEY,
        # 设置网络代理
        # 'proxy': {
        #     'http': 'xx',
        #     'https': 'xx'
        # },
        # 换成你的 bucket
        'bucket': request.project.bucket,
        # 换成 bucket 所在地区
        'region': request.project.bucket_region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            'name/cos:PostObject',
            # 分片上传
            'name/cos:InitiateMultipartUpload',
            'name/cos:ListMultipartUploads',
            'name/cos:ListParts',
            'name/cos:UploadPart',
            'name/cos:CompleteMultipartUpload'
        ],
        # 临时密钥生效条件，关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
        # "condition": {
        #     "ip_equal": {
        #         "qcs:ip": [
        #             "10.217.182.3/24",
        #             "111.21.33.72/24",
        #         ]
        #     }
        # }
    }

    try:
        sts = Sts(config)
        response = sts.get_credential()
        return JsonResponse(response)
    except Exception as e:
        print(e)


@csrf_exempt
def check_file_before_upload(request, pid):
    check_info = json.loads(request.body.decode('utf-8'))
    total_file_size = 0
    print(check_info)
    # 单文件大小验证
    for item in check_info:
        if int(item['size']) > 20 * 1024 * 1024:
            return JsonResponse({'status': False})

    # 文件总大小验证
    for item in check_info:
        total_file_size += int(item['size'])
    if total_file_size > 500 * 1024 * 1024:
        return JsonResponse({'status': False})

    return JsonResponse({'status': True})


@csrf_exempt
def check_file_after_upload(request, pid):
    from urllib.parse import urlparse, parse_qs
    check_info = request.POST
    print(type(check_info))
    print(check_info)
    form = FileSaveModelForm(data=request.POST)

    post_url = request.POST.get('url')
    # 解析URL
    parsed_url = urlparse(post_url)
    # 获取查询字符串参数
    query_parameters = parse_qs(parsed_url.query)
    # 获取名为'folder'的参数值
    folder_value = query_parameters.get('folder', [None])[0]

    if form.is_valid():
        form.instance.project = request.project
        form.instance.update_user = request.saas
        if folder_value is None:
            form.instance.parent = None
        else:
            parent_obj = FileBank.objects.filter(id=int(folder_value), file_type=2).first()
            form.instance.parent = parent_obj
        form.save()
        # 此处直接通过中间件创建的项目对象save()方法直接更新。也可以通过传统的方式，先查询数据库的原数据，加上file_size后再更新，但注意此时查询时要用select for update上一个写锁
        request.project.use_space += int(request.POST.get('file_size'))
        request.project.save()  # 直接对project对象进行save()操作，自动更新数据库，注意这里不能project.user_space进行操作，必须对整张表操作

        result = {
            'id': form.instance.id,
            'name': form.instance.name,
            'file_size': form.instance.file_size,
            'username': form.instance.update_user.username,
            'datetime': form.instance.update_datetime,
            'download_url': form.instance.id,

        }
        return JsonResponse({'status': True, 'result': result})
    print(form.errors)
    return JsonResponse({'status': False})


# 下载文件
def download_file(request, pid, fid):
    from saas.tools.tencent_cos import cos_download_file

    # 通过前端url的项目id与文件id找到需要下载的文件对象（数据库里
    file_obj = FileBank.objects.filter(id=fid, project_id=pid).first()

    # 调用腾讯的对象下载接口，返回一个二进制文件流
    res_binary_stream = cos_download_file(request.project.bucket, request.project.bucket_region, file_obj.key,
                                          file_obj.file_path)

    # 构建 HttpResponse 对象，将文件流作为响应内容，设置适当的响应头
    response = HttpResponse(res_binary_stream, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename={}'.format(file_obj.name)

    # 向前端返回响应，使浏览器开始下载
    return response

@csrf_exempt
def delete_file(request, pid):
    """删除文件"""
    from saas.tools.tencent_cos import delete_object
    fid = request.POST.get('fid')
    print(fid)
    file_obj = FileBank.objects.filter(project_id=pid, id=fid).first()
    delete_object(request.project.bucket, request.project.bucket_region, file_obj.key)
    file_obj.delete()
    return JsonResponse({'status': True})
