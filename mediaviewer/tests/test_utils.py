import mock

from django.test import TestCase

from mysite.settings import EMAIL_FROM_ADDR

from mediaviewer.utils import (
        getSomewhatUniqueID,
        humansize,
        sendMail,
        )

from mediaviewer.tests import helpers

SOMEWHAT_UNIQUE_TEST_ATTEMPTS = 100


class TestGetSomewhatUniqueID(TestCase):
    def test_valid(self):
        vals = set()

        for i in range(SOMEWHAT_UNIQUE_TEST_ATTEMPTS):
            int_val = int(getSomewhatUniqueID(), base=16)

            vals.add(int_val)

        self.assertEqual(
                len(vals),
                SOMEWHAT_UNIQUE_TEST_ATTEMPTS,
                'Expected to get {} vals. Only received {}'.format(
                    SOMEWHAT_UNIQUE_TEST_ATTEMPTS,
                    len(vals)))


class TestHumanSize(TestCase):
    def test_invalid_type(self):
        with self.assertRaises(TypeError):
            humansize('asdf')

    def test_0(self):
        self.assertEqual(
                humansize(0),
                '0 B')

    def test_100(self):
        self.assertEqual(
                humansize(100),
                '100 B')

    def test_1000(self):
        self.assertEqual(
                humansize(1000),
                '1000 B')

    def test_10000(self):
        self.assertEqual(
                humansize(10000),
                '9.77 KB')

    def test_100000(self):
        self.assertEqual(
                humansize(100000),
                '97.66 KB')

    def test_1000000(self):
        self.assertEqual(
                humansize(1000000),
                '976.56 KB')

    def test_10000000(self):
        self.assertEqual(
                humansize(10000000),
                '9.54 MB')

    def test_100000000(self):
        self.assertEqual(
                humansize(100000000),
                '95.37 MB')

    def test_1000000000(self):
        self.assertEqual(
                humansize(1000000000),
                '953.67 MB')

    def test_10000000000(self):
        self.assertEqual(
                humansize(10000000000),
                '9.31 GB')

    def test_100000000000(self):
        self.assertEqual(
                humansize(100000000000),
                '93.13 GB')

    def test_1000000000000(self):
        self.assertEqual(
                humansize(1000000000000),
                '931.32 GB')

    def test_10000000000000(self):
        self.assertEqual(
                humansize(10000000000000),
                '9.09 TB')


class TestSendMail(TestCase):
    def setUp(self):
        SMTP_patcher = mock.patch(
                'mediaviewer.utils.smtplib.SMTP')
        self.mock_SMTP = SMTP_patcher.start()
        self.addCleanup(SMTP_patcher.stop)

        MIMEMultipart_patcher = mock.patch(
                'mediaviewer.utils.MIMEMultipart')
        self.mock_MIMEMultipart = MIMEMultipart_patcher.start()
        self.addCleanup(MIMEMultipart_patcher.stop)

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

        self.assertEqual(expected, actual)
        self.mock_SMTP.assert_called_once_with(
                'localhost')
        self.mock_SMTP.return_value.sendmail.assert_called_once_with(
                EMAIL_FROM_ADDR,
                set([self.to_addr, self.staff_user.email]),
                self.mock_MIMEMultipart.return_value.as_string.return_value
                )
