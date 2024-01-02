from django.shortcuts import render, redirect
from app01.models import usersinfo
from biaodan import Create_user
import math


def show_users(request):
    from django.utils.safestring import mark_safe
    global page_str_list, html_str

    # 获取当前的页码
    request_page = int(request.GET.get("p", 1))

    # 获取当前搜索的关键字query，并把query放进数据库检索条件中，故分页建立在检索后的基础上，因此分页功能与搜索功能不在冲突
    query = request.GET.get("q",'')
    data_count = usersinfo.objects.filter(name__contains=query).count()

    pcs = 10
    show_pcs = 4
    page_num = math.ceil(data_count / pcs)
    page_str_list = []
    for i in range(1, page_num + 1):  # 形成一张页码列表，同时拼接query条件
        ele = f'<li class="page-item"><a class="page-link" href="?p={i}&q={query}">{i}</a></li>'
        page_str_list.append(ele)
    if request_page < show_pcs + 1:  # 判断当前页是否在show_pcs+1之前，若是则仅展示第1页-第show_pcs*2+1页
        page_str_list = page_str_list[0:show_pcs * 2 + 1]
    elif show_pcs + 1 <= request_page <= page_num - show_pcs:  # 判断当前页是否在正常需要缩进的区间内
        page_str_list = page_str_list[(request_page - show_pcs - 1):(request_page + 4)]
    elif request_page > page_num - show_pcs:  # 判断当前页是否在最后一页与2*(show_pcs)-1页之间
        page_str_list = page_str_list[-1 - (2 * show_pcs):]
    html_str = mark_safe("".join(page_str_list))

    start_pcs = (request_page - 1) * pcs + 1  # 需要展示的数据条数起点
    end_pcs = (request_page - 1) * pcs + pcs  # 需要展示的数据条数终点
    data_list = usersinfo.objects.filter(name__contains=query)[start_pcs - 1:end_pcs]  # -1是因为索引数比实际页码数少1

    return render(request, 'app01/show_users.html', {'data_list': data_list, 'html_str': html_str}, )
    # for i in range(105, 350):
    #     name = "xbh_" + str(i)
    #     password = "123_" + str(i)
    #     age = random.randrange(18,65)
    #     account = random.randrange(1000,15000)
    #     create_time = radar.random_date("2000-11-23", "2023-08-30")
    #     gender = 1
    #     depart_id = random.randrange(1, 6)
    #     usersinfo.objects.create(name=name, password=password, age=age, account=account, create_time=create_time,
    #                              gender=gender, depart_id=depart_id)


def create_user(request):
    create_user_form = Create_user()
    if request.method == "GET":
        return render(request, 'app01/create_user.html', {"create_user_form": create_user_form})
    else:
        create_user_form = Create_user(data=request.POST)
        if create_user_form.is_valid():
            create_user_form.save()
            return redirect('/erp/user_list')
        else:
            return "有误"


def delete_user(request, uid):
    delete_user_name = usersinfo.objects.filter(id=uid).delete()
    return redirect('/erp/user_list/')


def edit_user(request, uid):
    row_ob = usersinfo.objects.filter(id=uid).first()
    edit_user_form = Create_user(instance=row_ob)
    if request.method == "GET":
        return render(request, 'app01/edit_user.html', {"edit_user_form": edit_user_form})
    else:
        edit_user_form = Create_user(data=request.POST, instance=row_ob)  # instance=row_ob代表在原数据上更新，而非新增
        if edit_user_form.is_valid():
            edit_user_form.save()
            return redirect('/erp/user_list')
        else:
            return "有误"
