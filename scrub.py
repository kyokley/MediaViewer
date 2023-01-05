from django.contrib.auth.models import User


WERT66 = 'wert66'


def main():
    for user in User.objects.all():
        user.set_password(WERT66)
        user.save()


if __name__ == '__main__':
    main()
