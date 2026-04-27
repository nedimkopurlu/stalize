import sys


MESSAGE = """
Stalize backtester devre dışı bırakıldı.

Neden:
- Sistem için "asla simülasyon yok" kuralı benimsendi.
- Mevcut eski backtester, gerçek sinyal geçmişi yerine varsayımsal alım kurallarıyla
  sanal portföy simülasyonu yapıyordu.

Bu script ancak şu koşullar sağlandıktan sonra yeniden açılmalıdır:
1. Sinyal üretildiği günkü gerçek skorlar kalıcı olarak saklanmalı
2. Giriş/çıkış kuralları açık ve denetlenebilir olmalı
3. Gerçek benchmark ve kurumsal veri setiyle doğrulama yapılmalı

Şimdilik bu script bilinçli olarak çalıştırılmaz.
"""


def main() -> int:
    print(MESSAGE.strip())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
