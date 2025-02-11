from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import os
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta
import tempfile

class PfxParserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('parse_pfx')
        
        # テスト用の証明書を作成
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_certificates()

    def create_test_certificates(self):
        # 秘密鍵の生成
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # 証明書の作成
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"testuser"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=10)
        ).sign(private_key, hashes.SHA256())

        # PKCS#12の作成（パスワードあり）
        p12_path = os.path.join(self.temp_dir, 'test.p12')
        p12_data = serialization.pkcs12.serialize_key_and_certificates(
            name=b"test",
            key=private_key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(b"testpass")
        )
        with open(p12_path, 'wb') as f:
            f.write(p12_data)
        self.p12_path = p12_path

        # パスワードなしのPKCS#12も作成
        p12_no_pass_path = os.path.join(self.temp_dir, 'test_no_pass.p12')
        p12_no_pass_data = serialization.pkcs12.serialize_key_and_certificates(
            name=b"test",
            key=private_key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(p12_no_pass_path, 'wb') as f:
            f.write(p12_no_pass_data)
        self.p12_no_pass_path = p12_no_pass_path

    def test_successful_parse_with_password(self):
        with open(self.p12_path, 'rb') as f:
            response = self.client.post(self.url, {
                'file': f,
                'password': 'testpass'
            }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], 'testuser')

    def test_successful_parse_without_password(self):
        with open(self.p12_no_pass_path, 'rb') as f:
            response = self.client.post(self.url, {
                'file': f
            }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], 'testuser')

    def test_wrong_password(self):
        with open(self.p12_path, 'rb') as f:
            response = self.client.post(self.url, {
                'file': f,
                'password': 'wrongpass'
            }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'パスワードが間違っています。')

    def test_no_file_uploaded(self):
        response = self.client.post(self.url, {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'ファイルがアップロードされていません。')

    def test_invalid_file_format(self):
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            f.write(b'not a p12 file')
            f.seek(0)
            response = self.client.post(self.url, {
                'file': f
            }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'pfx/p12ファイルの解析に失敗しました。')

    def tearDown(self):
        # テスト用ファイルの削除
        if os.path.exists(self.p12_path):
            os.remove(self.p12_path)
        if os.path.exists(self.p12_no_pass_path):
            os.remove(self.p12_no_pass_path)
        os.rmdir(self.temp_dir)
