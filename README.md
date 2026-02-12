# 🧪 SDS → Excel AI Feldolgozó v3.0

Biztonsági adatlapok (SDS/MSDS) automatikus feldolgozása mesterséges intelligenciával.
**6 munkalap**, H/P mondatok kifejtve, védőeszköz specifikáció, kémiai kockázatértékelés.

## ✨ Funkciók

| Funkció | Leírás |
|---|---|
| **PDF → JSON** | GPT-4o kinyeri a 84 mezőt minden SDS-ből |
| **H/P kifejtés** | `H225 (Fokozottan tűzveszélyes folyadék és gőz)` formátum |
| **Kockázatértékelés** | 4×4 mátrix, színkódolt szintek (zöld/sárga/narancs/piros) |
| **Védőeszköz spec.** | Kesztyű típus, vastagság, áttörési idő, EN szabvány, szűrő típus |
| **6 munkalap** | Útmutató, Segédtáblák, Adatbázis, Kockázatértékelés, Expozíciós nyilv., Intézkedési terv |

## 📋 Munkalapok

1. **Útmutató** – Jogszabályi háttér (Mvt., Kbtv., CLP, REACH), jelölések
2. **Segédtáblák** – Kockázati mátrix, GHS piktogramok, valószínűségi/súlyossági skálák
3. **Veszélyes_anyag_adatbázis** – 84 oszlopos teljes nyilvántartás
4. **Kémiai_kockázatértékelés** – 29 oszlop, VxS mátrix, védőeszköz specifikáció, BEM
5. **Expozíciós_nyilvántartás** – Üres sablon Mvt. 63/A. § szerint
6. **Intézkedési_terv** – Előtöltve a kockázatértékelés alapján

## 🚀 Telepítés

```bash
# Klónozás / fájlok bemásolása
cd sds-processor

# Virtuális környezet (ajánlott)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Függőségek
pip install -r requirements.txt
```

## ⚙️ Konfiguráció

OpenAI API kulcs megadása (válassz egyet):

**A) Streamlit secrets (ajánlott):**
```bash
mkdir .streamlit
echo OPENAI_API_KEY = "sk-..." > .streamlit/secrets.toml
```

**B) Kézi megadás:** A bal oldali sávban közvetlenül beírható.

## ▶️ Futtatás

```bash
streamlit run sds_processor_v3.py
```

Megnyílik a böngészőben: `http://localhost:8501`

## 📁 Fájlstruktúra

```
sds-processor/
├── sds_processor_v3.py      # Fő alkalmazás (844 sor)
├── requirements.txt          # Python függőségek
├── README.md                 # Ez a fájl
└── .streamlit/
    └── secrets.toml          # API kulcs (opcionális)
```

## 💰 Költségek

- ~2 API hívás / SDS (adatkinyerés + kockázatértékelés)
- ~$0.25–0.35 / SDS (GPT-4o árazással)
- 40 SDS ≈ $10–14

## 📜 Jogszabályi háttér

- 1993. évi XCIII. tv. (Mvt.) – 54. § kockázatértékelés, 63/A. § expozíciós nyilvántartás
- 2000. évi XXV. tv. (Kbtv.) – kémiai biztonság
- 5/2020. (II. 6.) ITM rendelet – kémiai kóroki tényezők
- 25/2000. (IX. 30.) EüM-SzCsM rendelet – munkahelyek kémiai biztonsága
- 1272/2008/EK (CLP) – osztályozás, címkézés
- 1907/2006/EK (REACH) – regisztráció, értékelés

## 📌 Verzió

- **v3.0** (2026.02.12.) – Teljes minta-kompatibilis: 6 munkalap, H/P kifejtés, védőeszköz spec., kockázatértékelés
- v2.0 (2026.02.11.) – Alapverzió, 1 munkalap
