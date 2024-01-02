import random

from django.shortcuts import render
from biaodan import add_order_form
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from app01.models import Order


@csrf_exempt
def show_order(request):
    if request.method == "GET":
        form = add_order_form()
        data_list = Order.objects.all()
        return render(request, 'app01/show_order.html', context={'data_list': data_list, 'form': form})

    # 当请求为POST时，是AJAX请求，此处根据AJAX中传过来的oid到数据库获取该行数据，再将数据JsonResponse回前端，在前端中用JS向表单中设置默认值
    row_obj = Order.objects.filter(oid=request.POST.get('oid')).values().first()
    if row_obj:
        # row_obj为字典类型
        return JsonResponse({'status': True, 'row_obj': row_obj})
    return JsonResponse({'status': False, 'errors': '订单不存在'})


@csrf_exempt
def add_order(request):
    form = add_order_form(data=request.POST)
    if form.is_valid():
        form.instance.oid = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
        form.instance.admin_id = request.session.get('erp_info_dict')['id']
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'errors': form.errors})


@csrf_exempt
def edit_order(request):
    oid = request.POST.get('oid')
    row_obj = Order.objects.filter(oid=oid).first()
    form = add_order_form(data=request.POST, instance=row_obj)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})
