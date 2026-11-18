# Django API’yi Coolify’da yayınlama

1. Coolify’da **Production → New Resource → PostgreSQL** yolunu kullan. Hetzner sunucusunu ve Django uygulamasıyla aynı destination ağını seç. Erişimi **Private** bırak, PostgreSQL’i başlat ve **General → Postgres URL (internal)** bilgilerini aç. [Coolify PostgreSQL belgeleri](https://coolify.io/docs/databases/postgresql)
2. GitHub kaynağından `faultechh-lab/cinarkombiyedekparca` deposunu ekle. Branch `main`, Build Pack `Docker Compose`, Base Directory `/` ve Docker Compose Location `/compose.coolify.external-db.yaml` olsun. **Advanced → Docker compose → Predefined network** bölümünde **Connect To Predefined Network** seçeneğini aç. [Coolify Compose belgeleri](https://coolify.io/docs/applications/builds/docker-compose#compose-networking)
3. `api` DNS kaydını Hetzner sunucusuna yönlendir. Coolify’da HTTPS alan adını `api` servisine ve `8080` iç portuna bağla. Dış adres örneği `https://api.cinarkombiyedekparca.com`.
4. **Environment Variables** bölümünde aşağıdaki değerleri gir ve **Deploy**’a bas. Django başlangıçta migrasyonları uygular ve statik dosyaları toplar.

| Değişken | Değer |
| --- | --- |
| `SITE_DOMAIN` | API alan adı, örneğin `api.cinarkombiyedekparca.com` |
| `DJANGO_SECRET_KEY` | `openssl rand -hex 32` ile üretilebilen rastgele bir değer |
| `DB_HOST` | Internal URL’deki sunucu adı |
| `DB_PORT` | Internal URL’deki port, genellikle `5432` |
| `DB_NAME` | PostgreSQL veritabanı adı |
| `DB_USER` | PostgreSQL kullanıcı adı |
| `DB_PASSWORD` | PostgreSQL parolası |
| `CSRF_EXTRA_ORIGINS` | Frontend’in HTTPS kök adresi. Birden fazla adresi virgülle ayır. |

Django ile birlikte bir PostgreSQL container’ı başlatmak istersen `/compose.coolify.yaml` dosyasını seç ve `DB_PASSWORD` değerini belirle. Bu dosya PostgreSQL’i `db_data` biriminde saklar.

## İlk çalıştırma ve doğrulama

Coolify’daki `backend` container terminalinden yönetici hesabını oluştur.

```sh
python manage.py createsuperuser
```

Boş veritabanına örnek kategorileri, ürünleri ve görselleri yüklemek için aşağıdaki komutu çalıştır. Komut mevcut kataloğun tamamını örneklerle değiştirir.

```sh
python manage.py replace_demo_catalog --replace
```

API alan adında `/healthz`, `/api/categories/` ve `/api/products/` yollarını aç. Django’nun üretim ayarlarını `python manage.py check --deploy --fail-level ERROR` ile denetle. Frontend servisi için `DJANGO_ORIGIN` değerine API’nin HTTPS kök adresini gir.

## Güncelleme ve yedekler

Coolify’daki GitHub App için **Advanced → Deployment → Auto deploy** ayarını **Deploy on push (webhooks)** olarak seç. `main` dalındaki güncellemeler yeni deploy’u başlatır. Veritabanı yedeğini PostgreSQL kaynağından al. Yüklenen katalog görselleri için `media` birimini de yedekle. [Coolify PostgreSQL yedekleri](https://coolify.io/docs/databases/postgresql#back-up-and-restore-postgresql)
