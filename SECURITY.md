# MERAK güvenlik notları

MERAK henüz deneysel bir Android uygulamasıdır. GitHub Actions tarafından üretilen
`app-debug.apk` dosyaları **üretim sürümü değildir**. Derleme başarısı uygulamanın
gerçek telefonda güvenlik testinden geçtiği anlamına gelmez.

## Güncel güvenlik yaklaşımı
- Kişisel notlar, ruh hâli ve ilgi alanları telefondaki uygulama alanında saklanır.
- Uygulama yalnızca Türkçe Vikipedi'den HTTPS üzerinden genel bilgi çeker.
- Uygulamada hesap, parola, reklam SDK'sı veya izleme analitiği bulunmaz.
- İnternetten gelen bilgiler metin olarak gösterilir; bağlantılar yalnızca
  `https://tr.wikipedia.org` alan adına açılabilir.
- Android izinleri, imza kontrolü ve kaynak dosyası bütünlüğü her derlemede incelenir.
- Ana dalın GitHub Actions iş akışı yalnızca içerik okuma yetkisiyle çalışır.

## Henüz çözülmesi gereken önemli konular
1. **Kalıcı imzalama:** Debug APK imza anahtarı farklı derlemelerde değişebilir.
   Üretim dağıtımı için özel, güvenli saklanan ve yedeklenen bir imzalama anahtarı gerekir.
   Bu anahtar **asla** herkese açık depoya eklenmemelidir.
2. **Veri kaybı riski:** Uygulama silinirse yerel notlar ve ilerleme kaybolabilir.
   Güvenli, kullanıcı kontrolündeki bir dışa/içe aktarma özelliği geliştirilmeden
   eski sürümü kaldırmak önerilmez.
3. **Gerçek cihaz testi:** Uygulama açılışı, içeriğin yenilenmesi, ağ hataları,
   çevrimdışı çalışma ve ekranların erişilebilirliği gerçek Android cihazlarda test edilmelidir.
4. **İçerik doğruluğu:** Vikipedi metinleri değişebilir veya zaman zaman hatalı olabilir.
   Bilgi doğruluğu için kaynak bağlantısı kullanıcıya görünür olmalı; kişisel sağlık
   ve hukuki kararlar için tek kaynak olarak kullanılmamalıdır.
5. **Depo görünürlüğü:** Proje şu anda herkese açıktır. Bu tek başına telefonun
   güvenliğini bozmaz. Ancak özel görseller veya gizli kodlar eklenmeden önce
   görünürlük kararı yeniden gözden geçirilmelidir.

## Dağıtım kontrol listesi
- CI derlemesi, APK imza doğrulaması ve izin denetimleri başarılı.
- Android'de güvenilir güncelleme imzası yapılandırılmış.
- Sürüm numarası artırılmış.
- Veri kaybı ve değişiklikler kullanıcıya açıklanmış.
- APK yalnızca güvenilir yayımlama kanalından sağlanıyor.
- Üretim için debug modundan çıkılmış, bağımlılık ve kod denetimi yapılmış.

Güvenlik sorunları için kamuya açık issue içine şifre, erişim anahtarı veya özel
kullanıcı verisi **yazmayın**.
