import pytest

from django.conf import settings

from mediaviewer.utils import (
    getSomewhatUniqueID,
    humansize,
    sendMail,
    checkSMTPServer,
    query_param_to_bool,
        )

from mediaviewer.tests import helpers

SOMEWHAT_UNIQUE_TEST_ATTEMPTS = 100


class TestGetSomewhatUniqueID:
    def test_valid(self):
        vals = set()

        for i in range(SOMEWHAT_UNIQUE_TEST_ATTEMPTS):
            int_val = int(getSomewhatUniqueID(), base=16)

            vals.add(int_val)

        assert len(vals) == SOMEWHAT_UNIQUE_TEST_ATTEMPTS, f'Expected to get {SOMEWHAT_UNIQUE_TEST_ATTEMPTS} vals. Only received {len(vals)}'


class TestHumanSize:
    def test_invalid_type(self):
        with pytest.raises(TypeError):
            humansize('asdf')

    def test_0(self):
        assert humansize(0) == '0 B'

    def test_100(self):
        assert humansize(100) == '100 B'

    def test_1000(self):
        assert humansize(1000) == '1000 B'

    def test_10000(self):
        assert humansize(10000) == '9.77 KB'

    def test_100000(self):
        assert humansize(100000) == '97.66 KB'

    def test_1000000(self):
        assert humansize(1000000) == '976.56 KB'

    def test_10000000(self):
        assert humansize(10000000) == '9.54 MB'

    def test_100000000(self):
        assert humansize(100000000) == '95.37 MB'

    def test_1000000000(self):
        assert humansize(1000000000) == '953.67 MB'

    def test_10000000000(self):
        assert humansize(10000000000) == '9.31 GB'

    def test_100000000000(self):
        assert humansize(100000000000) == '93.13 GB'

    def test_1000000000000(self):
        assert humansize(1000000000000) == '931.32 GB'

    def test_10000000000000(self):
        assert humansize(10000000000000) == '9.09 TB'


@pytest.mark.django_db
class TestSendMail:
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.mock_SMTP = mocker.patch(
                'mediaviewer.utils.smtplib.SMTP')

        self.mock_MIMEMultipart = mocker.patch(
                'mediaviewer.utils.MIMEMultipart')

        self.staff_user = helpers.create_user(is_staff=True)
        self.normal_user = helpers.create_user(
                username='normal_user',
                email='b@c.com')

        self.to_addr = 'test@example.com'

    def test_valid(self):
        expected = None
        actual = sendMail(
                self.to_addr,
                'test_subject',
                'test_text',
                )

        assert expected == actual
        self.mock_SMTP.assert_called_once_with(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
        )
        self.mock_SMTP.return_value.sendmail.assert_called_once_with(
                settings.EMAIL_FROM_ADDR,
                set([self.to_addr, self.staff_user.email]),
                self.mock_MIMEMultipart.return_value.as_string.return_value
                )
        self.mock_SMTP.return_value.close.assert_called_once_with()


class BaseSMTPServerTestCase:
    def create_mocks(self, mocker):
        self.mock_Telnet = mocker.patch(
                'mediaviewer.utils.telnetlib.Telnet')

        self.mock_settings = mocker.patch(
            'mediaviewer.utils.settings')

        self.mock_settings.EMAIL_HOST = 'test_host'
        self.mock_settings.EMAIL_PORT = 'test_port'


class TestCheckSMTPServer(BaseSMTPServerTestCase):
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.create_mocks(mocker)

        self.mock_settings.BYPASS_SMTPD_CHECK = False

    def test_smtpd_check(self):
        expected = None
        actual = checkSMTPServer()

        assert expected == actual
        self.mock_Telnet.assert_called_once_with(
                host='test_host',
                port='test_port')
        self.mock_Telnet.return_value.close.assert_called_once_with()


class TestSkipCheckSMTPServer(BaseSMTPServerTestCase):
    @pytest.fixture(autouse=True)
    def setUp(self, mocker):
        self.create_mocks(mocker)

        self.mock_settings.BYPASS_SMTPD_CHECK = True

    def test_bypass_smtpd_check(self):
        expected = None
        actual = checkSMTPServer()

        assert expected == actual
        assert not self.mock_Telnet.called


class TestQueryParamToBool:
    def test_true(self):
        assert query_param_to_bool(True)
        assert query_param_to_bool('True')
        assert query_param_to_bool('true')
        assert query_param_to_bool('T')
        assert query_param_to_bool('t')
        assert query_param_to_bool('yes')
        assert query_param_to_bool('y')

    def test_false(self):
        assert not query_param_to_bool(False)
        assert not query_param_to_bool('False')
        assert not query_param_to_bool('false')
        assert not query_param_to_bool('F')
        assert not query_param_to_bool('f')
        assert not query_param_to_bool('no')
        assert not query_param_to_bool('n')

    def test_raise(self):
        assert query_param_to_bool(None) is None
        assert query_param_to_bool('') is None
