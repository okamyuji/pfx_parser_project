from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.fernet import InvalidToken
import io

@api_view(['POST'])
@parser_classes([MultiPartParser])
def parse_pfx(request):
    """
    POSTリクエストで送信されたpfx/p12ファイルを解析し、CNからユーザーIDを抽出して返すAPIエンドポイント。
    """
    print("request.FILES:", request.FILES)
    print("request.POST:", request.POST)
    if 'file' not in request.FILES:
        return Response({'error': 'ファイルがアップロードされていません。'}, status=status.HTTP_400_BAD_REQUEST)

    pfx_file = request.FILES['file']
    pfx_password = request.data.get('password', None)

    try:
        pfx_data = pfx_file.read()
        pfx_password_bytes = pfx_password.encode('utf-8') if pfx_password else None

        # pfx/p12ファイルをロード
        try:
            pkcs12_bundle = pkcs12.load_key_and_certificates(
                pfx_data, pfx_password_bytes
            )
        except ValueError as ve:
            error_message = str(ve)
            # パスワードエラーの場合の処理
            if "bad password" in error_message.lower() or "bad decrypt" in error_message.lower():
                return Response({'error': 'パスワードが間違っています。'}, status=status.HTTP_400_BAD_REQUEST)
            # その他のValueErrorは一般的な解析エラーとして扱う
            return Response({'error': 'pfx/p12ファイルの解析に失敗しました。'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # パスワードなしで再試行する前に、一般的な解析エラーとして扱う
            return Response({'error': 'pfx/p12ファイルの解析に失敗しました。'}, status=status.HTTP_400_BAD_REQUEST)

        # タプルから証明書を取得 (private_key, certificate, ca_certs)
        _, certificate, _ = pkcs12_bundle

        if certificate is None:
            return Response({'error': '証明書が見つかりませんでした。'}, status=status.HTTP_400_BAD_REQUEST)

        # Subject DN から CN を取得
        subject = certificate.subject
        common_name_rdn = subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)

        if not common_name_rdn:
            user_id = "CN not found" # CNが見つからない場合はエラーではなく、その旨を返すように変更
        else:
            user_id = common_name_rdn[0].value

        return Response({'user_id': user_id}, status=status.HTTP_200_OK)

    except Exception as e:
        print(e) # エラーログはコンソールに出力 (本番環境ではロギング設定を推奨)
        return Response({'error': 'pfx/p12ファイルの解析に失敗しました。'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
