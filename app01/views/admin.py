from django.shortcuts import render, HttpResponse, redirect
from app01.models import admin
from biaodan import Create_admin_form, Reset_pwd_admin_form
from django.utils.safestring import mark_safe
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
from io import BytesIO


def check_code(width=120, height=30, char_length=5,
               font_file='D:\\Python\\python_work\\django_project\\app01\\views\\Monaco.ttf', font_size=28):
    code = []
    img = Image.new(mode='RGB', size=(width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img, mode='RGB')

    def rndChar():
        """
        生成随机字母
        :return:
        """
        # return str(random.randint(0, 9))
        return chr(random.randint(65, 90))

    def rndColor():
        """
        生成随机颜色
        :return:
        """
        return (random.randint(0, 255), random.randint(10, 255), random.randint(64, 255))

    # 写文字
    font = ImageFont.truetype(font_file, font_size)
    for i in range(char_length):
        char = rndChar()
        code.append(char)
        h = random.randint(0, 4)
        draw.text((i * width / char_length, h), char, font=font, fill=rndColor())

    # 写干扰点
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())

    # 写干扰圆圈
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=rndColor())

    # 画干扰线
    for i in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)

        draw.line((x1, y1, x2, y2), fill=rndColor())

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img, ''.join(code)


def homepage(request):
    return render(request, 'app01/homepage.html')


def login(request):
    if request.method == 'GET':
        # 判断用户是否有cookies
        exist = request.session.get('info_dict')
        if exist:
            return redirect('/erp/user_list')
        return render(request, 'app01/login.html')

    # 首先进行验证码校验
    input_check_code = request.POST.get('check_code')
    if input_check_code != request.session.get('check_code'):
        check_code_error = '<div style="color:red;font-size:10px;margin-bottom: 10px;margin_top:-10px">验证码错误</div>'
        check_code_error = mark_safe(check_code_error)
        return render(request, 'app01/login.html', {"check_code_error": check_code_error})

    # 用户名密码校验
    input_username = request.POST.get('username')
    input_password = request.POST.get('password')
    exist = admin.objects.filter(username=input_username, password=input_password).first()
    if exist:
        current_id = exist.id
        request.session['erp_info_dict'] = {'id': current_id, 'username': input_username}
        request.session.set_expiry(60 * 60 * 24)
        return redirect('/erp/user_list/')

    error_div = '<div style="color:red;font-size:10px;margin-bottom: 10px;margin_top:-10px">用户名或密码错误</div>'
    error_div = mark_safe(error_div)
    return render(request, 'app01/login.html', {"error_div": error_div})


def generate_code(request):
    """ 生成图片验证码 """
    img, code_string = check_code()
    request.session["check_code"] = code_string
    request.session.set_expiry(60)

    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def show_admin(request):
    # for i in range(1, 20):
    #     admin.objects.create(username="xbh", password="123456")
    data_list = admin.objects.all()
    return render(request, "app01/show_admin.html", {'data_list': data_list})


def create_admin(request):
    if request.method == "GET":
        form = Create_admin_form()
        return render(request, "app01/create_admin.html", {"form": form})

    form = Create_admin_form(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/erp/admin_list/')
    return render(request, "app01/create_admin.html", {"form": form})


def resetpwd_admin(request, uid):
    if request.method == "GET":
        form = Reset_pwd_admin_form()
        return render(request, "app01/resetpwd_admin.html", {"uid": uid, "form": form})

    form = Reset_pwd_admin_form(data=request.POST)
    if form.is_valid():
        admin.objects.filter(id=uid).update(password=request.POST.get('password'))
        return redirect('/erp/admin_list/')
    return render(request, "app01/resetpwd_admin.html", {"uid": uid, "form": form})


def register(request):
    return render(request, 'app01/register.html')
