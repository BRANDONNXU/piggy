from django.forms import RadioSelect

from app01.models import admin
from saas.models import Users, Project, Wiki, FileBank, IssuesType, Module, ProjectUser, Issues
from django import forms
import app01
import saas
from django.core.exceptions import ValidationError


class BoostrapModelForm(forms.ModelForm):
    exclude_style = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.exclude_style:
                continue
            field.widget.attrs = {"class": "container form-control", "style": "display:inline-block"}


class BoostrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "container form-control", "style": "display:inline-block"}


class Create_user(BoostrapModelForm):
    class Meta:
        model = app01.models.usersinfo
        fields = ['id', 'name', 'password', 'age', 'account', 'create_time', 'gender', 'depart']
        # widgets = {}
        # for field in fields:
        #     temp = {field: forms.TextInput(attrs={"class": "form-control"})}
        #     widgets.update(temp)


class Edit_department_form(BoostrapModelForm):
    class Meta:
        model = app01.models.Department
        fields = ["id", "depart", "manager"]

    # def __str__(self):
    #     return self.template_name


class Create_admin_form(BoostrapModelForm):
    confirm_pwd = forms.CharField(label="确认密码", widget=forms.PasswordInput(render_value=True))

    class Meta:
        model = app01.models.admin
        fields = "__all__"

    # 检查密码确认是否正确
    def clean_confirm_pwd(self):
        pwd_01 = self.cleaned_data.get('password')
        pwd_02 = self.cleaned_data.get('confirm_pwd')
        if pwd_01 == pwd_02:
            return pwd_02
        raise ValidationError("密码不一致")

    # 检查用户名是否重复
    def clean_username(self):
        create_username = self.cleaned_data.get('username')
        exist = admin.objects.filter(username=create_username).first()
        if exist:
            raise ValidationError('用户名已存在')
        return create_username


class Reset_pwd_admin_form(BoostrapForm):
    password = forms.CharField(label="新密码", widget=forms.PasswordInput(render_value=True), required=True)
    confirm_pwd = forms.CharField(label="确认密码", widget=forms.PasswordInput(render_value=True), required=True)

    def clean_confirm_pwd(self):
        pwd_01 = self.cleaned_data.get('password')
        pwd_02 = self.cleaned_data.get('confirm_pwd')
        if pwd_01 == pwd_02:
            return pwd_02
        raise ValidationError("密码不一致")


class add_order_form(BoostrapModelForm):
    oid = forms.CharField(disabled=True, required=False)

    class Meta:
        model = app01.models.Order
        fields = '__all__'
        exclude = ['admin']


class saas_register_form(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "name": "email",
                "type": "email",
                "id": "id_email",
                "class": "form-control",
                "placeholder": "Email",
                "required": True,
                "autofocus": True,
            }
        )
    )

    mobile_phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "name": "mobile_phone",
                "type": "text",
                "id": "id_mobile_phone",
                "class": "form-control",
                "placeholder": "mobile_phone",
                "required": True,
                "autofocus": True,
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "name": "password",
                "type": "password",
                "id": "id_password",
                "class": "form-control",
                "placeholder": "Password",
                "required": True,
                "autofocus": True,
            }
        )
    )
    confirm_pwd = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "name": "confirm_pwd",
                "type": "password",
                "id": "id_confirm_pwd",
                "class": "form-control",
                "placeholder": "confirm_password",
                "required": True,
                "autofocus": True,
            }
        )
    )

    # code = forms.CharField(
    #     widget=forms.TextInput(
    #         attrs={
    #             "name": "code",
    #             "type": "code",
    #             "id": "id_code",
    #             "class": "form-control",
    #             "placeholder": "confirm_password",
    #             "required": True,
    #             "autofocus": True,
    #         }
    #     )
    # )

    class Meta:
        model = saas.models.Users
        fields = ['email', 'password', 'confirm_pwd', 'mobile_phone']

    def clean_confirm_pwd(self):
        pwd_01 = self.cleaned_data.get('password')
        pwd_02 = self.cleaned_data.get('confirm_pwd')
        if pwd_01 == pwd_02:
            return pwd_02
        raise ValidationError("密码不一致")

    def clean_email(self):
        input_email = self.cleaned_data.get('email')
        exist = Users.objects.filter(email=input_email).exists()
        if exist:
            raise ValidationError('该邮箱已被注册')
        return input_email

    def clean_mobile_phone(self):
        input_mobile_phone = self.cleaned_data.get('mobile_phone')
        exist = Users.objects.filter(mobile_phone=input_mobile_phone).exists()
        if exist:
            raise ValidationError('该手机号码已被注册')
        return input_mobile_phone


class ColorRadioSelect(RadioSelect):
    template_name = "widgets/color_radio.html"
    option_template_name = "widgets/color_radio_option.html"


class saas_create_project_form(BoostrapModelForm):
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    exclude_style = ['color']

    class Meta:
        model = saas.models.Project
        fields = ['name', 'color', 'desc']
        widgets = {
            'desc': forms.Textarea,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'})
        }

    def clean_name(self):
        input_name = self.cleaned_data.get('name')
        creator = Users.objects.filter(id=self.request.session['saas_info_dict']['id']).first()
        exist = Project.objects.filter(name=input_name, creator=creator).first()
        if exist:
            raise ValidationError('您已创建过该项目')
        return input_name


class wiki_form(BoostrapModelForm):
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        total_data_list = [("", "请选择")]
        # 一种限制下拉框可选项范围的方法
        data_list = Wiki.objects.filter(project=request.project).values_list('id', 'title')
        total_data_list.extend(data_list)
        self.fields['parent'].choices = total_data_list

    class Meta:
        model = saas.models.Wiki
        fields = '__all__'
        exclude = ['project', 'depth']


class FileFolderModelForm(BoostrapModelForm):
    def __init__(self, request, parent_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_obj = parent_obj

    class Meta:
        model = saas.models.FileBank
        fields = ['name']

    def clean_name(self):
        input_name = self.cleaned_data.get('name')

        if not self.parent_obj:
            # 根目录下重名
            if FileBank.objects.filter(name=input_name, project=self.request.project, parent__isnull=True).first():
                raise ValidationError('文件夹已存在')
        else:
            # 同父目录下重名
            if FileBank.objects.filter(name=input_name, project=self.request.project, parent=self.parent_obj).first():
                raise ValidationError('文件夹已存在')
        return input_name


class FileSaveModelForm(BoostrapModelForm):
    ETag = forms.CharField(label="ETag")

    class Meta:
        model = saas.models.FileBank
        fields = '__all__'

    def clean_file_path(self):
        file_path = 'https://' + self.cleaned_data['file_path']
        return file_path

    def clean_ETag(self):
        return self.cleaned_data['ETag']


class issue_form(BoostrapModelForm):
    class Meta:
        model = saas.models.Issues
        fields = '__all__'
        exclude = ['project', 'creator']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加问题时的数据初始化

        # 1. 获取当前项目所有的问题类型
        issue_type_list_for_this_project = IssuesType.objects.filter(project=request.project).values_list('id',
                                                                                                          'title')  # (id,title）组成一个元组
        self.fields['issues_type'].choices = issue_type_list_for_this_project

        # 2. 获取当前项目所有的模块
        module_list_for_this_project = Module.objects.filter(project=request.project).values_list('id',
                                                                                                  'title')  # (id,title）组成一个元组
        self.fields['module'].choices = module_list_for_this_project

        # 3. 获取当前项目的创建者与所有参与者
        total_user_list = [(request.project.creator.id, request.project.creator.username), ]
        attention_for_this_project = ProjectUser.objects.filter(project=request.project).values_list('user_id',
                                                                                                     'user__username')
        total_user_list.extend(attention_for_this_project)
        self.fields['assign'].choices = total_user_list
        self.fields['attention'].choices = total_user_list

        # 4.获取当前项目已创建的问题
        total = [('', '无'), ]
        parent_issues_list_for_this_project = Issues.objects.filter(project=request.project).values_list('id',
                                                                                                         'subject')
        total.extend(parent_issues_list_for_this_project)
        self.fields['parent'].choices = total


class IssueReplayModelForm(BoostrapModelForm):
    class Meta:
        model = saas.models.IssuesReply
        fields = ['content', 'reply']


class InviteModelForm(BoostrapModelForm):
    class Meta:
        model = saas.models.ProjectInvite
        fields = ['period', 'count']
