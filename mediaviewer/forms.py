import re

from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template import loader

NUMBER_REGEX = re.compile(r"[0-9]")
CHAR_REGEX = re.compile(r"[a-zA-Z]")


class InvalidEmailException(Exception):
    pass


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
