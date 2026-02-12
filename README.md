# 🧪 SDS → Excel AI Feldolgozó Rendszer

Automatikus biztonsági adatlap (SDS/MSDS) feldolgozó rendszer, amely:
- **PDF SDS fájlokat** dolgoz fel (1-100 fájl batch-ben)
- **AI-val kinyeri** a strukturált adatokat (85 mező/SDS)
- **Többnyelvű**: magyar, angol, német SDS-eket is feldolgoz → magyar kimenet
- **Online kutatással** kiegészíti a hiányzó adatokat
- **Excel fájlt generál** a szabványos mintafájl formátumában
- **Verzió-ellenőrzéssel** jelzi az elavult SDS-eket

## 🚀 Telepítés és indítás

### Lokális futtatás
```bash
pip install -r requirements.txt
streamlit run sds_processor_v2.py
```

### Streamlit Cloud deploy
1. Fork-old ezt a repót
2. Streamlit Cloud → New App → válaszd ki a repót
3. Settings → Secrets → add meg az `OPENAI_API_KEY`-t
4. Deploy!

## 📁 Fájlstruktúra
```
├── sds_processor_v2.py          # Fő alkalmazás (többnyelvű + online kutatás)
├── sds_version_checker.py       # SDS verzió-ellenőrző modul
├── sds_template_schema.json     # Adatbázis séma (85 mező)
├── requirements.txt             # Python függőségek
├── .streamlit/
│   ├── config.toml              # Streamlit konfiguráció
│   └── secrets.toml.example     # Minta a titkos kulcsokhoz
└── README.md                    # Ez a fájl
```

## ⚙️ Beállítás
1. Szerezz OpenAI API kulcsot: https://platform.openai.com/api-keys
2. Add meg a kulcsot a Streamlit Secrets-ben vagy `.streamlit/secrets.toml`-ban
3. Opcionálisan: töltsd fel a minta Excel fájlt sablonként

## 💰 Költségek
- ~0.20-0.30 USD / SDS feldolgozás (GPT-4o API)
- Streamlit Community Cloud: **ingyenes**
