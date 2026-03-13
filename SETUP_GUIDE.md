# SDS AI Feldolgozó v3.2 – Telepítési és konfigurációs útmutató

## Fizetési rendszer: Stripe + Barion párhuzamosan

A felhasználó az alkalmazás betöltésekor választhat a két fizetési mód közül:
- **Stripe** – nemzetközi bankkártyás fizetés (Visa, Mastercard, Apple Pay, Google Pay)
- **Barion Smart Gateway** – magyar fizetési rendszer (bankkártya, Barion tárca, átutalás)

---

## 1. lépés: Stripe beállítása

### 1.1 Stripe regisztráció
1. Regisztrálj: https://dashboard.stripe.com/register
2. Add meg a vállalkozási adataidat (Safety Expert EV)
3. Aktiváld a fiókod

### 1.2 Termék és fizetési link létrehozása
1. Dashboard → Products → Add Product
   - Név: "SDS AI Feldolgozó – egyszeri használat"
   - Ár: 2990 HUF (vagy amit szeretnél)
   - Típus: One-time (egyszeri) VAGY Recurring (előfizetés)
2. Dashboard → Payment Links → Create Payment Link
   - Válaszd ki a létrehozott terméket
   - Másold ki a linket (pl. `https://buy.stripe.com/test_xxxxx`)

### 1.3 API kulcsok
1. Dashboard → Developers → API Keys
2. Másold ki:
   - **Secret key** (teszt): `sk_test_...`
   - **Secret key** (éles): `sk_live_...`

### 1.4 secrets.toml frissítése
```toml
payment_provider = "stripe"
testing_mode = true
stripe_api_key_test = "sk_test_XXXXXXX"
stripe_link_test = "https://buy.stripe.com/test_XXXXXXX"
stripe_api_key = "sk_live_XXXXXXX"
stripe_link = "https://buy.stripe.com/XXXXXXX"
```

---

## 2. lépés: Google OAuth beállítása (Stripe-hoz szükséges)

A st-paywall a Streamlit natív bejelentkezését használja (OIDC), amihez Google OAuth kell.

### 2.1 Google Cloud Console
1. Nyisd meg: https://console.cloud.google.com
2. Hozz létre egy új projektet (pl. "SDS-AI-App")
3. APIs & Services → Credentials → Create Credentials → OAuth Client ID
4. Application type: Web application
5. Authorized redirect URI: `https://APPNEV.streamlit.app/oauth2callback`
6. Másold ki a Client ID-t és Client Secret-et

### 2.2 secrets.toml frissítése
```toml
[auth]
redirect_uri = "https://APPNEV.streamlit.app/oauth2callback"
cookie_secret = "VELETLENSZERU_32_KARAKTERES_SZOVEG"
client_id = "XXXXXXX.apps.googleusercontent.com"
client_secret = "GOCSPX-XXXXXXX"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

---

## 3. lépés: Barion beállítása

### 3.1 Barion regisztráció
1. Regisztrálj: https://secure.barion.com/Registration
2. Add meg a vállalkozási adataidat
3. Hozz létre egy Shop-ot (Bolt):
   - Dashboard → Shop-ok → Új shop
   - Név: "SDS AI Feldolgozó"
   - Redirect URL: `https://APPNEV.streamlit.app/`
   - Callback URL: `https://APPNEV.streamlit.app/barion-callback`

### 3.2 POSKey megszerzése
- A Shop beállításaiban találod a POSKey-t (GUID formátumú)

### 3.3 Teszt környezet
- Barion teszt: https://secure.test.barion.com
- Teszt API: `https://api.test.barion.com`
- Éles API: `https://api.barion.com`

### 3.4 secrets.toml frissítése
```toml
barion_poskey = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
barion_payee_email = "BSomoracz@gmail.com"
barion_api_url = "https://api.test.barion.com"
barion_redirect_url = "https://APPNEV.streamlit.app/?barionPaymentId={PaymentId}"
barion_callback_url = "https://APPNEV.streamlit.app/barion-callback"
```

---

## 4. lépés: Streamlit Cloud telepítés

### 4.1 GitHub repo frissítése
1. Töltsd fel az összes fájlt a GitHub repo-ba:
   - `sds_processor_v3.py`
   - `sds_version_checker.py`
   - `requirements.txt`
   - `.streamlit/secrets.toml` → NE töltsd fel Git-re!

### 4.2 Streamlit Cloud secrets
1. https://share.streamlit.io → az alkalmazásod → Settings → Secrets
2. Másold be a `secrets.toml` tartalmát ide
3. Ez a biztonságos módja a kulcsok tárolásának (nem kerül Git-re)

### 4.3 requirements.txt
Az alkalmazás automatikusan telepíti:
- `st-paywall` (Stripe integráció)
- `clientapi-barion` (Barion Python SDK)
- `streamlit[auth]` (OIDC támogatás)
- `requests` (Barion API hívások)

---

## 5. lépés: Iframe beágyazás a safetyexpert.hu-ba

1. Másold a `msds-feldolgozo/index.html` fájlt a `public_html/msds-feldolgozo/` mappába
2. Szerkeszd az iframe `src` attribútumot → cseréld ki a Streamlit Cloud URL-re
3. A `online-szolgaltatasok.html`-ben már aktiválva van az "SDS AI Feldolgozó" kártya

---

## 6. lépés: Élesítés

Ha a tesztelés sikeres:
1. `secrets.toml`-ban: `testing_mode = false`
2. `barion_api_url` → `https://api.barion.com`
3. Stripe kulcsoknál az éles (live) kulcsokat használd
4. Barion: a Shop-ot aktiváld éles módba a Barion dashboardon

---

## Számlázás (opcionális, de ajánlott)

### Számlázz.hu integráció
- https://www.szamlazz.hu – regisztráció + API kulcs
- Automatikus számlakiállítás minden sikeres fizetés után
- Integrálható mind Stripe webhook-kal, mind Barion callback-kal
- NAV online számla kompatibilis

Ez egy következő fejlesztési lépés – jelenleg a fizetési rendszer működik számla nélkül is,
de egyéni vállalkozóként a számlakiállítás kötelező. Ideiglenesen kézi számlázás is megoldás.

---

## Hibaelhárítás

| Probléma | Megoldás |
|----------|----------|
| Stripe bejelentkezés nem működik | Ellenőrizd a Google OAuth redirect URI-t |
| Barion hiba | Ellenőrizd a POSKey-t és az API URL-t (teszt vs. éles) |
| iframe nem töltődik | Ellenőrizd a Streamlit Cloud URL-t az index.html-ben |
| "st.user not found" | `pip install streamlit[auth]` és frissítsd a Streamlit verziót |
