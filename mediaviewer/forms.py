from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (SetPasswordForm,
                                       PasswordChangeForm,
                                       PasswordResetForm,
                                       )
from django.contrib.auth.tokens import default_token_generator
from mysite.settings import MINIMUM_PASSWORD_LENGTH
import re

NUMBER_REGEX = re.compile(r'[0-9]')
CHAR_REGEX = re.compile(r'[a-zA-Z]')

class InvalidPasswordException(Exception):
    pass

class InvalidEmailException(Exception):
    pass

def _has_number_validator(val):
    return bool(NUMBER_REGEX.search(val))

def _has_char_validator(val):
    return bool(CHAR_REGEX.search(val))

def _is_long_enough_validator(val):
    return len(val) >= MINIMUM_PASSWORD_LENGTH

def validate_reset_user_password(user,
                                 new_password,
                                 can_login=True
                                 ):
    if not _has_number_validator(new_password):
        raise InvalidPasswordException('Password is too weak. Valid passwords must contain at least one numeric character.')

    if not _has_char_validator(new_password):
        raise InvalidPasswordException('Password is too weak. Valid passwords must contain at least one alphabetic character.')

    if not _is_long_enough_validator(new_password):
        raise InvalidPasswordException('Password is too weak. Valid passwords must be at least %s characters long.' % MINIMUM_PASSWORD_LENGTH)

def _is_email_unique(user, val):
    return (user.email.lower() != val.lower() and
                not User.objects.filter(email__iexact=val).exists())

def validate_email(user, email):
    if not _is_email_unique(user, email):
        raise InvalidEmailException('Email already exists on system. Please try another.')


class MVSaveBase(SetPasswordForm):
    def save(self, commit=True):
        settings = self.user.settings()
        settings.force_password_change = False
        settings.can_login = True
        settings.save()
        super(MVSaveBase, self).clean(commit=commit)

class MVSetPasswordForm(MVSaveBase):
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        try:
            validate_reset_user_password(self.user,
                                         password1,
                                         )
        except InvalidPasswordException, e:
            raise forms.ValidationError(str(e),
                                        code='password_exception')

        return password1


class MVPasswordChangeForm(PasswordChangeForm, MVSaveBase):
    def clean_new_password1(self):
        old_password = self.cleaned_data['old_password']
        password1 = self.cleaned_data.get('new_password1')
        if old_password == password1:
            raise InvalidPasswordException('New and old passwords must be different')

        try:
            validate_reset_user_password(self.user,
                                         password1,
                                         )
        except InvalidPasswordException, e:
            raise forms.ValidationError(str(e),
                                        code='password_exception')

        return password1

class FormlessPasswordReset(PasswordResetForm):
    def __init__(self, user, email):
        self.cleaned_data = {'email': email}
        self.user = user

    def clean_email(self):
        super(FormlessPasswordReset, self).clean_email()
        try:
            validate_email(self.user,
                           self.cleaned_data['email'],
                           )
        except InvalidEmailException, e:
            raise forms.ValidationError(str(e),
                                        code='email_exception')

    def save(self,
             domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False,
             token_generator=default_token_generator,
             from_email=None,
             request=None):
        self.user.email = self.cleaned_data['email']
        self.user.save()

        super(FormlessPasswordReset, self).save(self,
                                                domain_override=domain_override,
                                                subject_template_name=subject_template_name,
                                                email_template_name=email_template_name,
                                                use_https=use_https,
                                                token_generator=token_generator,
                                                from_email=from_email,
                                                request=request,
                                                )
