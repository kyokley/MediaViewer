from django import forms
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    SetPasswordForm,
    PasswordChangeForm,
    PasswordResetForm,
)
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings as conf_settings
import re

NUMBER_REGEX = re.compile(r"[0-9]")
CHAR_REGEX = re.compile(r"[a-zA-Z]")


class InvalidPasswordException(Exception):
    pass


class InvalidEmailException(Exception):
    pass


def _has_number_validator(val):
    return bool(NUMBER_REGEX.search(val))


def _has_char_validator(val):
    return bool(CHAR_REGEX.search(val))


def _is_long_enough_validator(val):
    return len(val) >= conf_settings.MINIMUM_PASSWORD_LENGTH


def validate_reset_user_password(user, new_password, can_login=True):
    if not _has_number_validator(new_password):
        raise InvalidPasswordException(
            "Password is too weak. "
            "Valid passwords must contain at least one numeric character."
        )

    if not _has_char_validator(new_password):
        raise InvalidPasswordException(
            "Password is too weak. "
            "Valid passwords must contain at least one alphabetic character."
        )

    if not _is_long_enough_validator(new_password):
        raise InvalidPasswordException(
            f"Password is too weak. "
            f"Valid passwords must be at least "
            f"{conf_settings.MINIMUM_PASSWORD_LENGTH} characters long."
        )


def change_user_password(
    user, old_password, new_password, confirm_new_password, can_login=True
):
    if not user.check_password(old_password):
        raise InvalidPasswordException("Incorrect password")

    if new_password != confirm_new_password:
        raise InvalidPasswordException("New passwords do not match")

    if old_password == new_password:
        raise InvalidPasswordException("New and old passwords must be different")

    validate_reset_user_password(user, new_password, can_login=can_login)
    user.set_password(new_password)
    settings = user.settings()
    settings.force_password_change = False
    settings.can_login = can_login
    settings.save()
    user.save()


class MVSaveBase(SetPasswordForm):
    def save(self, commit=True):
        settings = self.user.settings()
        settings.force_password_change = False
        settings.can_login = True
        settings.save()
        super(MVSaveBase, self).save()


class MVSetPasswordForm(MVSaveBase):
    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")
        try:
            validate_reset_user_password(
                self.user,
                password1,
            )
        except InvalidPasswordException as e:
            raise forms.ValidationError(str(e), code="password_exception")

        return password1


class MVPasswordChangeForm(PasswordChangeForm, MVSaveBase):
    def clean_new_password1(self):
        if self.errors:
            return

        old_password = self.cleaned_data["old_password"]
        password1 = self.cleaned_data.get("new_password1")
        if old_password == password1:
            raise InvalidPasswordException("New and old passwords must be different")

        try:
            validate_reset_user_password(
                self.user,
                password1,
            )
        except InvalidPasswordException as e:
            raise forms.ValidationError(str(e), code="password_exception")

        return password1


class PasswordResetFormWithBCC(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        bcc = [user.email for user in User.objects.filter(is_staff=True) if user.email]

        email_message = EmailMultiAlternatives(
            subject, body, from_email, [to_email], bcc=bcc
        )

        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

        email_message.send()


class FormlessPasswordReset(PasswordResetFormWithBCC):
    def __init__(self, user, email):
        self.data = {"email": email}
        self.cleaned_data = {}
        self.user = user

    def clean_email(self):
        email = self.data["email"]
        try:
            self.cleaned_data["email"] = email
        except InvalidEmailException as e:
            raise forms.ValidationError(str(e), code="email_exception")
        return email

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
    ):
        self.user.email = self.clean_email()
        self.user.save()

        super(FormlessPasswordReset, self).save(
            domain_override=domain_override,
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            use_https=use_https,
            token_generator=token_generator,
            from_email=from_email,
            request=request,
        )


def notify_admin_of_new_user(
    new_user,
    from_email=None,
    html_email_template_name=None,
):
    """
    Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    if from_email is None:
        from_email = conf_settings.EMAIL_FROM_ADDR

    context = {"user": new_user}
    subject = loader.render_to_string("mediaviewer/auth0_create_new_user_subject.txt")
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    body = loader.render_to_string(
        "mediaviewer/auth0_create_new_user_email.html", context
    )
    to_emails = [
        user.email for user in User.objects.filter(is_staff=True) if user.email
    ]

    email_message = EmailMultiAlternatives(subject, body, from_email, to_emails)

    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, "text/html")

    email_message.send()
