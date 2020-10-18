import string
import random
from django.core.mail import send_mail as django_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from users.models import ResetCode


def random_str():
    chars = string.ascii_letters + string.digits
    variable = ''.join(random.sample(chars, 8))
    return variable


def send_email(email):
    user = get_user_model()
    account = user.objects.get(email=email)
    random_code = random_str()

    ResetCode.objects.create(code=random_code, user=account)

    email_title = '忘记密码'
    a_href = '{0}/reset_password/?code={1}'.format(settings.FRONT_URL, random_code)
    email_body = "请点击下面的链接修改密码: <a href='{}'>重置密码</a>".format(a_href)

    status = django_mail(email_title, '', settings.EMAIL_FROM, [email], html_message=email_body)
    return status
