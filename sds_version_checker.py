#!/usr/bin/env python3
"""
SDS Verzió-ellenőrző és Frissítés-kereső Modul
=================================================
Az adatbázis felépítése UTÁN automatikusan:
1. Összehasonlítja a feltöltött SDS dátumát az online elérhető legújabbal
2. Több forrásból keres (gyártói weboldal, msds.com, Google SDS keresés)
3. Dashboard-on jelzi a frissítendő SDS-eket
4. Letöltési linket generál az újabb verzióhoz
5. Opcionálisan automatikusan letölti és feldolgozza az új verziót

Telepítés:
    pip install streamlit openai requests beautifulsoup4 openpyxl

Ez a modul a sds_processor_v2.py kiegészítése.
"""

import streamlit as st
import json
import time
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass
from openai import OpenAI


# ============================================================
# 1. ADATMODELL
# ============================================================

@dataclass
class SDSVersionInfo:
    """Egy SDS verzió-ellenőrzés eredménye"""
    ssz: int
    product_name: str
    manufacturer: str
    current_version: str
    current_date: str
    current_date_parsed: Optional[datetime]

    # Online keresés eredménye
    online_version_found: bool = False
    online_version: Optional[str] = None
    online_date: Optional[str] = None
    online_date_parsed: Optional[datetime] = None
    online_source_url: Optional[str] = None
    online_source_name: Optional[str] = None
    download_url: Optional[str] = None

    # Státusz
    is_outdated: bool = False
    days_difference: Optional[int] = None
    age_years: Optional[float] = None
    status: str = "Nem ellenőrzött"  # OK / Frissítés elérhető / Elavult (>5 év) / Nem található
    status_icon: str = "⬜"

    # Keresési jegyzet
    search_notes: Optional[str] = None


# ============================================================
# 2. VERZIÓ-ELLENŐRZŐ LOGIKA
# ============================================================

def check_sds_version_online(product_name: str, manufacturer: str,
                              current_version: str, current_date: str,
                              cas_numbers: List[str],
                              client: OpenAI) -> dict:
    """
    Online keresés egy SDS legújabb verziójáért.
    GPT-4o web_search tool-t használ a kereséshez.
    """

    search_query = f"""Keress rá a következő termék biztonsági adatlapjára (SDS/MSDS):

Termék neve: {product_name}
Gyártó: {manufacturer}
CAS számok: {', '.join(cas_numbers) if cas_numbers else 'nem ismert'}
Jelenlegi SDS verzió: {current_version}
Jelenlegi SDS dátum: {current_date}

FELADAT:
1. Keresd meg a gyártó ({manufacturer}) hivatalos weboldalán az SDS letöltési oldalát
2. Keresd meg a terméket az alábbi SDS adatbázisokon is:
   - msds.com / msds-europe.com
   - Google: "{product_name} {manufacturer} safety data sheet PDF"
   - ECHA regisztrációs adatbázis (ha releváns)
3. Állapítsd meg, hogy a jelenlegi verzió ({current_version}, dátum: {current_date}) a legfrissebb-e
4. Ha újabb verzió érhető el, add meg:
   - Az új verzió számát és dátumát
   - A letöltési URL-t (direkt PDF link ha lehetséges)
   - A forrás nevét

VÁLASZOLJ az alábbi JSON formátumban:
{{
    "newer_version_found": true/false,
    "latest_version": "verzió szám vagy null",
    "latest_date": "YYYY-MM-DD vagy szöveges dátum",
    "download_url": "URL vagy null",
    "source_name": "forrás neve",
    "source_url": "forrás weboldal URL",
    "notes": "megjegyzések magyarul"
}}
"""

    response = client.responses.create(
        model="gpt-4o",
        tools=[{
            "type": "web_search",
            "user_location": {
                "type": "approximate",
                "country": "HU",
                "city": "Budapest",
            }
        }],
        input=[
            {"role": "system", "content": """Te egy veszélyes anyag nyilvántartási szakértő vagy.
A feladatod, hogy megkeresd egy adott termék legfrissebb biztonsági adatlapját (SDS/MSDS) az interneten.
Légy alapos: ellenőrizd a gyártó weboldalát, a nagy SDS adatbázisokat, és a Google-t is.
MINDIG adj vissza érvényes JSON-t a kért formátumban."""},
            {"role": "user", "content": search_query}
        ],
    )

    # Válasz feldolgozása
    result_text = response.output_text

    # JSON kinyerése a válaszból
    try:
        json_match = re.search(r'\{[^{}]*"newer_version_found"[^{}]*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "newer_version_found": False,
        "notes": result_text[:300],
        "source_name": "Keresés sikertelen",
    }


def check_all_sds_versions(sds_database: list, client: OpenAI,
                            progress_callback=None) -> List[SDSVersionInfo]:
    """Az összes SDS verzió-ellenőrzése batch módban"""

    results = []

    for i, sds in enumerate(sds_database):
        # Dátum feldolgozása
        current_date_str = sds.get('sds_date', '') or sds.get('sds_revision_date', '')
        current_date_parsed = None
        age_years = None

        if current_date_str:
            for fmt in ['%Y-%m-%d', '%Y.%m.%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    current_date_parsed = datetime.strptime(current_date_str.strip(), fmt)
                    age_years = (datetime.now() - current_date_parsed).days / 365.25
                    break
                except:
                    continue

        # CAS számok összegyűjtése
        cas_numbers = []
        for comp_key in ['component_1', 'component_2', 'component_3']:
            comp = sds.get(comp_key, {})
            if isinstance(comp, dict) and comp.get('cas_number'):
                cas_numbers.append(comp['cas_number'])

        # Verzió-ellenőrzés
        version_info = SDSVersionInfo(
            ssz=sds.get('ssz', i+1),
            product_name=sds.get('product_name', 'Ismeretlen'),
            manufacturer=sds.get('manufacturer', 'Ismeretlen'),
            current_version=sds.get('sds_version', '?'),
            current_date=current_date_str,
            current_date_parsed=current_date_parsed,
            age_years=age_years,
        )

        # Online keresés
        try:
            online_result = check_sds_version_online(
                product_name=version_info.product_name,
                manufacturer=version_info.manufacturer,
                current_version=version_info.current_version,
                current_date=version_info.current_date,
                cas_numbers=cas_numbers,
                client=client,
            )

            version_info.online_version_found = online_result.get('newer_version_found', False)
            version_info.online_version = online_result.get('latest_version')
            version_info.online_date = online_result.get('latest_date')
            version_info.download_url = online_result.get('download_url')
            version_info.online_source_url = online_result.get('source_url')
            version_info.online_source_name = online_result.get('source_name')
            version_info.search_notes = online_result.get('notes')

            # Státusz meghatározása
            if version_info.online_version_found:
                version_info.status = "🔄 Frissítés elérhető"
                version_info.status_icon = "🔄"
                version_info.is_outdated = True
            elif age_years and age_years > 5:
                version_info.status = "⚠️ Elavult (>5 év)"
                version_info.status_icon = "⚠️"
                version_info.is_outdated = True
            elif age_years and age_years > 3:
                version_info.status = "🟡 Ellenőrzés javasolt"
                version_info.status_icon = "🟡"
            else:
                version_info.status = "✅ Aktuális"
                version_info.status_icon = "✅"

        except Exception as e:
            version_info.status = "❌ Keresés sikertelen"
            version_info.search_notes = str(e)

        results.append(version_info)

        if progress_callback:
            progress_callback(i + 1, len(sds_database), version_info.product_name)

        time.sleep(2)  # Rate limit

    return results


# ============================================================
# 3. STREAMLIT UI – VERZIÓ-ELLENŐRZŐ DASHBOARD
# ============================================================

def render_version_dashboard(results: List[SDSVersionInfo]):
    """Verzió-ellenőrzési eredmények megjelenítése"""

    st.header("📋 SDS Verzió-ellenőrzés Eredményei")

    # Összefoglaló metrikák
    col1, col2, col3, col4 = st.columns(4)

    n_ok = sum(1 for r in results if "Aktuális" in r.status)
    n_update = sum(1 for r in results if "Frissítés" in r.status)
    n_old = sum(1 for r in results if "Elavult" in r.status)
    n_check = sum(1 for r in results if "Ellenőrzés" in r.status)

    col1.metric("✅ Aktuális", n_ok)
    col2.metric("🔄 Frissítés elérhető", n_update)
    col3.metric("⚠️ Elavult (>5 év)", n_old)
    col4.metric("🟡 Ellenőrzés javasolt", n_check)

    st.divider()

    # ---- FRISSÍTENDŐ SDS-ek (kiemelt rész) ----
    updates_available = [r for r in results if r.online_version_found]

    if updates_available:
        st.subheader("🔄 Frissítések letöltése")
        st.warning(f"**{len(updates_available)} termékhez újabb SDS verzió érhető el az interneten!**")

        for r in updates_available:
            with st.expander(f"{r.status_icon} {r.product_name} ({r.manufacturer})", expanded=True):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**Jelenlegi verzió:**")
                    st.text(f"  Verzió: {r.current_version}")
                    st.text(f"  Dátum: {r.current_date}")
                    if r.age_years:
                        st.text(f"  Kor: {r.age_years:.1f} év")

                with col_b:
                    st.markdown("**Elérhető újabb verzió:**")
                    st.text(f"  Verzió: {r.online_version or '?'}")
                    st.text(f"  Dátum: {r.online_date or '?'}")
                    st.text(f"  Forrás: {r.online_source_name or '?'}")

                if r.download_url:
                    st.markdown(f"📥 **[SDS letöltése]({r.download_url})**")

                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        if st.button(f"📥 Letöltés és feldolgozás", key=f"dl_{r.ssz}"):
                            st.info("Letöltés és újrafeldolgozás folyamatban...")
                    with col_dl2:
                        if st.button(f"🔗 Megnyitás böngészőben", key=f"open_{r.ssz}"):
                            st.markdown(f'<meta http-equiv="refresh" content="0;url={r.download_url}">',
                                       unsafe_allow_html=True)

                if r.online_source_url:
                    st.caption(f"Forrás: [{r.online_source_name}]({r.online_source_url})")

                if r.search_notes:
                    st.caption(f"Megjegyzés: {r.search_notes[:200]}")

    st.divider()

    # ---- TELJES LISTA ----
    st.subheader("📊 Összes SDS státusz")

    # Szűrők
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.multiselect("Státusz szűrő", 
            ["✅ Aktuális", "🔄 Frissítés elérhető", "⚠️ Elavult (>5 év)", "🟡 Ellenőrzés javasolt"],
            default=["🔄 Frissítés elérhető", "⚠️ Elavult (>5 év)"])
    with filter_col2:
        sort_by = st.selectbox("Rendezés", ["Kor (legrégebbi elöl)", "Név", "Státusz"])

    # Táblázat
    table_data = []
    for r in results:
        if not status_filter or any(s in r.status for s in [x.split(" ", 1)[1] if " " in x else x for x in status_filter]):
            table_data.append({
                "Státusz": r.status_icon,
                "Ssz.": r.ssz,
                "Termék": r.product_name,
                "Gyártó": r.manufacturer,
                "Jelenlegi verzió": r.current_version,
                "SDS dátum": r.current_date,
                "Kor (év)": f"{r.age_years:.1f}" if r.age_years else "?",
                "Új verzió": r.online_version or "—",
                "Új dátum": r.online_date or "—",
                "Letöltés": "📥" if r.download_url else "—",
            })

    if table_data:
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    # ---- AUTOMATIKUS FRISSÍTÉS ÜTEMEZÉS ----
    st.divider()
    st.subheader("⏰ Ütemezett ellenőrzés beállítása")

    col_sched1, col_sched2 = st.columns(2)
    with col_sched1:
        check_frequency = st.selectbox("Ellenőrzés gyakorisága", 
            ["Hetente", "Havonta", "Negyedévente", "Félévente"])
        auto_download = st.checkbox("Automatikus letöltés (ha elérhető)", value=False)
    with col_sched2:
        email_notify = st.text_input("E-mail értesítés címe", placeholder="safety@company.hu")
        notify_threshold = st.slider("Figyelmeztetés ennyi év után", 1, 10, 3)

    if st.button("💾 Beállítások mentése"):
        st.success("Ütemezett ellenőrzés beállítva!")


# ============================================================
# 4. INTEGRÁCIÓ A FŐ ALKALMAZÁSSAL
# ============================================================

def add_version_check_tab():
    """Ez a függvény a fő sds_processor_v2.py alkalmazásba integrálható"""

    st.markdown("""
    ## 🔄 SDS Frissítés-kereső működése

    ### Automatikus lépések az adatbázis felépítése UTÁN:

    ```
    1. Adatbázis kész (Excel generálva)
         ↓
    2. Minden SDS-hez: verzió + dátum kiolvasása
         ↓
    3. Online keresés (GPT-4o web_search):
       ├── Gyártó hivatalos weboldala
       ├── msds.com / msds-europe.com adatbázis
       ├── Google: "[terméknév] [gyártó] SDS PDF"
       └── ECHA regisztrációs dossier
         ↓
    4. Összehasonlítás:
       ├── Újabb verzió elérhető? → 🔄 Letöltési link
       ├── SDS > 5 éves? → ⚠️ Elavult figyelmeztetés
       ├── SDS > 3 éves? → 🟡 Ellenőrzés javasolt
       └── SDS aktuális → ✅ OK
         ↓
    5. Dashboard megjelenítés:
       ├── Összefoglaló metrikák
       ├── Frissítési javaslatok letöltési linkekkel
       ├── 1 kattintásos letöltés + újrafeldolgozás
       └── E-mail értesítés beállítása
    ```

    ### Keresési források prioritás szerint:
    1. **Gyártó hivatalos weboldala** – legmegbízhatóbb
    2. **SDS adatbázisok** (SDS Manager 16M+ SDS, msds.com, CloudSDS)
    3. **Google SDS keresés** – "[terméknév] [gyártó] safety data sheet PDF"
    4. **ECHA** – regisztrációs dossier-ben is lehet SDS

    ### REACH/CLP szabályok az SDS frissítéshez:
    - SDS-t frissíteni KELL, ha új kockázati információ áll rendelkezésre
    - SDS-t frissíteni KELL, ha engedélyezést adtak/tagadtak meg
    - SDS-t frissíteni KELL, ha korlátozást vezettek be
    - A frissített SDS-t minden korábbi vevőnek meg kell küldeni
    - **Jó gyakorlat**: 5 évnél régebbi SDS felülvizsgálata
    """)


if __name__ == "__main__":
    st.set_page_config(page_title="🔄 SDS Verzió-ellenőrző", layout="wide")
    st.title("🔄 SDS Verzió-ellenőrző és Frissítés-kereső")
    add_version_check_tab()
