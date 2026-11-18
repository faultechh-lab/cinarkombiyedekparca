# Üretim kurulumu

## Coolify ile önce backend

Hetzner sunucusundaki Coolify’da Git deposu üzerinden **Docker Compose** uygulaması oluştur. Base Directory olarak depo kökünü, Docker Compose Location olarak `/compose.coolify.yaml` seç. HTTPS alan adını `api` servisine bağla ve iç portu `8080` olarak gir. Örnek alan adı `https://api.cinarkombiyedekparca.com:8080`. Dışarıdan kullanılan bağlantı `https://api.cinarkombiyedekparca.com` olur. [Coolify Compose belgeleri](https://coolify.io/docs/applications/builds/docker-compose#configure-public-services)

Coolify ortam değişkenlerinde `SITE_DOMAIN` değerine yalnızca API’nin alan adını yaz. `DJANGO_SECRET_KEY` ve `DB_PASSWORD` için ayrı, rastgele değerler kullan. `DB_NAME` ve `DB_USER` varsayılanları kullanılabilir. `CSRF_EXTRA_ORIGINS`, frontend bağlantısı kurulduğunda HTTPS adresiyle doldurulabilir. Coolify HTTPS’i sonlandırır, `api` servisi Django isteklerini ve kalıcı medya birimindeki görselleri sunar.

İlk dağıtımda backend terminalinden yönetici hesabını oluştur.

```sh
python manage.py createsuperuser
```

Boş bir üretim veritabanına örnek kataloğu yüklemek için aynı terminalden aşağıdaki komutu çalıştır. Komut mevcut katalog kayıtlarının tamamını örneklerle değiştirir.

```sh
python manage.py replace_demo_catalog --replace
```

API adresinde `/healthz`, `/api/categories/` ve `/api/products/` yollarını açarak dağıtımı doğrula. Frontend bağlantısı için HTTPS API kök adresi yeterlidir.

### Coolify’da ayrı PostgreSQL kaynağı

Production ortamında **New Resource → PostgreSQL** ile veritabanı oluştur. Django uygulamasıyla aynı Hetzner sunucusunu ve aynı Coolify destination ağını seç. PostgreSQL’i başlat ve General bölümündeki **Postgres URL (internal)** değerini kullan. Veritabanı erişimi Private olarak kalabilir. [Coolify PostgreSQL belgeleri](https://coolify.io/docs/databases/postgresql)

Backend uygulamasının **Docker Compose Location** alanına `/compose.coolify.external-db.yaml` yaz. **Advanced → Docker compose → Predefined network** bölümünde **Connect To Predefined Network** seçeneğini aç. API alan adı ve `8080` portu için yukarıdaki ayarları kullan. [Coolify ağ belgeleri](https://coolify.io/docs/core/networking-in-coolify#how-private-container-traffic-works)

PostgreSQL bağlantısı için Coolify’ın gösterdiği sunucu adını `DB_HOST`, portu `DB_PORT` (varsayılan `5432`), database adını `DB_NAME`, kullanıcı adını `DB_USER` ve veritabanı parolasını `DB_PASSWORD` olarak gir. `SITE_DOMAIN`, `DJANGO_SECRET_KEY` ve `CSRF_EXTRA_ORIGINS` ayarları yukarıdaki gibidir. Django ilk başlangıçta migrasyonları bu veritabanına uygular.

## Tek sunucuda frontend ve backend

Bu kurulum tek bir Linux VPS üzerinde Docker Compose kullanır. Caddy dışarıya HTTPS sunar. Node, Django API’sinden aldığı verilerle katalog sayfalarını ve site haritasını sunar. PostgreSQL verileri ile yüklenen görseller ayrı kalıcı birimlerde tutulur.

## İlk çalıştırma

1. Sunucuda Docker Engine ve Compose eklentisi kurulu olmalı. Birincil alan adı ve varsa yönlendirme alanı sunucuya çözülmeli. Caddy için TCP 80 ve 443 erişilebilir olmalı.
2. Proje kökünde `cp .env.production.example .env.production` komutuyla ortam dosyasını oluştur. `chmod 600 .env.production` ile erişimi kısıtla. `openssl rand -hex 32` komutunu iki kez çalıştırıp farklı değerleri `DJANGO_SECRET_KEY` ve `DB_PASSWORD` alanlarına yaz. Alan adları farklıysa `SITE_DOMAIN` ve `REDIRECT_DOMAIN` değerlerini birlikte güncelle.
3. Backend ve veritabanını başlat, ardından yönetici hesabını oluştur.

```sh
docker compose --env-file .env.production up -d --build backend
docker compose --env-file .env.production exec backend python manage.py createsuperuser
```

Backend ilk açılışta migrasyonları çalıştırır ve statik dosyaları toplar. Ardından Gunicorn başlar.

## Mevcut katalog ve görselleri taşıma

Yerel makinede proje kökünden aşağıdaki iki çıktıyı al ve sunucunun proje kökündeki `.deploy/` klasörüne aktar.

```sh
mkdir -p .deploy
(cd backend && venv/bin/python manage.py dumpdata products.Category products.Product --indent 2) > .deploy/catalog.json
tar -C backend/media -czf .deploy/catalog-media.tar.gz .
```

Sunucuda ilk kurulum sırasında aynı iki dosyayı yükle.

```sh
docker compose --env-file .env.production exec -T backend tar -xzf - -C /app/backend/media < .deploy/catalog-media.tar.gz
docker compose --env-file .env.production exec -T backend python manage.py loaddata --format=json - < .deploy/catalog.json
docker compose --env-file .env.production up -d --build
docker compose --env-file .env.production ps
```

Bu adım yereldeki örnek ürün ve kategori kayıtlarını, açıklamalarını, URL’lerini ve görsellerini taşır. Üretim yöneticisi sunucudaki `createsuperuser` komutuyla oluşturulur. Örnek katalog ve temsili görsellerin yayına uygunluğunu gözden geçir.

## Yayın doğrulaması

- Birincil HTTPS adresini, kategori ve ürün sayfalarını ve `/sitemap.xml` çıktısını aç.
- Yönlendirme alanında bir ürün URL’sinin yol ve sorgu parametreleri korunarak birincil alana gittiğini kontrol et.
- `/giris/` üzerinden yönetici girişi yap. Panelde kategori ve ürünlerin, görsellerin ve çıkışın erişilebilir olduğunu doğrula.
- Üretim ayarları için Django denetimini çalıştır.

```sh
docker compose --env-file .env.production exec backend python manage.py check --deploy --fail-level ERROR
```

HSTS birincil alan adında bir saat etkindir. Django’nun alt alan adı ve preload denetimleri uyarı verebilir.

## Katalog yedeği ve güncelleme

```sh
mkdir -p .deploy
docker compose --env-file .env.production exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > .deploy/catalog-database.sql
docker compose --env-file .env.production exec -T backend tar -C /app/backend/media -czf - . > .deploy/catalog-media.tar.gz
docker compose --env-file .env.production up -d --build
```

Güncelleme mevcut veritabanı ve medya birimlerini yeniden kullanır. Üretim ortam dosyasını ve yedekleri kaynak kod deposu dışında sakla.
