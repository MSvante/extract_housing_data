# Hus-søgningssystem - Aarhus området

Dette projekt hjælper med at finde det perfekte hus i Aarhus-området. Systemet scraper boligdata fra boliga.dk, beregner en score baseret på vores præferencer, og præsenterer resultaterne gennem en interaktiv webapp.

## 🎯 Projektmål

- **Geografisk fokus**: Kun områder med togforbindelse til Aarhus Banegård (almindelig tog eller letbane)
- **Boligtype**: Kun huse (ikke lejligheder, rækkehuse, etc.)
- **Automatisering**: Daglig scraping og scoring af nye boliger
- **Notifikationer**: Advarsler ved interessante nye boliger
- **Platform**: Lokal kørsel med DuckDB og Pandas

## 🚀 Hurtig Start (Automatisk Opsætning)

`start.py` scriptet inkluderer nu automatisk miljø-opsætning! Kør blot:

```bash
python3 start.py full
```

Dette vil automatisk:
- Tjekke Python version (3.8+ påkrævet)
- Oprette et virtuelt miljø hvis intet eksisterer
- Installere alle dependencies fra requirements.txt
- Oprette nødvendige mapper (data, logs)
- Køre pipeline og starte web appen

## 📋 Forudsætninger

- Python 3.8+
- Internetforbindelse til scraping af boliga.dk

## 🛠️ Manuel Installation (hvis nødvendigt)

Hvis du foretrækker manuel opsætning eller oplever problemer med automatisk opsætning:

1. **Klon/naviger til projekt-mappen:**
   ```bash
   cd /home/mser/code/repos/housing_data_extract
   ```

2. **Opret virtuelt miljø:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # På Windows: venv\Scripts\activate
   ```

3. **Installer dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Opret nødvendige mapper:**
   ```bash
   mkdir -p data logs
   ```

## 📊 Scoring Algoritme (Detaljeret)

Hver bolig scores nu på **8 parametre** med lige vægtning (max 80 point):

**Globale faktorer (samme for alle huse):**
- **Energiklasse** (10 point max): A=10, B=8, C=6, D=4, E=2, F/G=0, UKENDT=3
- **Afstand til tog** (10 point max): Beregnet via GPS koordinater til S-tog og letbane

**Relative faktorer (sammenlignet inden for samme postnummer):**
- **Grundstørrelse** (10 point max): Større grund = højere score relativt til området
- **Husstørrelse** (10 point max): Større hus = højere score relativt til området  
- **Priseffektivitet** (10 point max): Lavere m²-pris = højere score relativt til området
- **Byggeår** (10 point max): Nyere hus = højere score relativt til området
- **Kælderareal** (10 point max): Større kælder = højere score relativt til området
- **Dage på marked** (10 point max): Færre dage = højere score relativt til området

**Total max score**: 80 point

## 🚀 Status opdatering

### ✅ Completeret:
1. **Migrering til lokal kørsel** - DuckDB og Pandas pipeline implementeret og testet
2. **Data extraction modernisering** - Alle nye felter ekstrakteret og valideret
3. **Forbedret scoring algoritme** - Implementeret og integreret i pipeline
4. **Streamlit app forbedringer** - Lokal version med nye filtre og score breakdown
5. **Repository cleanup** - Fjernet alle legacy Databricks filer og scripts

### 🔄 I gang:
- Performance optimering af scraping
- Email notifikationssystem
- Automatisk deployment til produktionsserver

## 📋 Data eksempel fra boliga.dk

```json
{
  "id": 2041515,
  "latitude": 56.31307,
  "longitude": 10.04435,
  "propertyType": 1,
  "priceChangePercentTotal": -9,
  "energyClass": "C",
  "price": 1450000,
  "rooms": 6,
  "size": 182,
  "lotSize": 1532,
  "buildYear": 1957,
  "city": "Hadsten",
  "isForeclosure": false,
  "zipCode": 8370,
  "street": "Skanderborgvej 16",
  "squaremeterPrice": 7967,
  "daysForSale": 625,
  "basementSize": 30,
  "images": [
    {
      "id": 2041515,
      "url": "https://i.boliga.org/dk/500x/2041/2041515.jpg"
    }
  ]
}
```

## 🎯 Næste skridt

1. ✅ **Opdater data extraction** til at inkludere alle relevante felter - **FULDFØRT**
2. ✅ **Implementer forbedret scoring** med energimærke og afstand til tog - **FULDFØRT**
3. ✅ **Migrer til DuckDB** og pandas-baseret processing - **FULDFØRT**
4. **Sæt notifikationssystem op** med email alerts
5. **Implementer automatisk scheduling** på produktionsserver
6. **Performance optimering** og memory usage forbedringer

## 📁 Projekt Struktur

```
housing_data_extract/
├── start.py                      # 🎯 HOVED STARTUP SCRIPT
├── README.md                     # Dette dokument  
├── requirements.txt             # Python dependencies
│
├── app/                         # 🖥️ Streamlit webapp
│   ├── __init__.py
│   └── app_local.py            # Streamlit interface
│
├── pipeline/                    # ⚙️ Data pipeline
│   ├── __init__.py
│   └── run_pipeline.py         # Pipeline orkestrering
│
├── scripts/                     # 📜 Automatiserings-scripts
│   ├── __init__.py
│   └── scheduler.py            # Automatiseret scheduling
│
├── src/                        # 🔧 Core moduler
│   ├── __init__.py
│   ├── extract_listings_local.py   # Data extraction
│   ├── transform_listings_local.py # Data transformation & scoring
│   └── database_local.py           # DuckDB management
│
├── data/                       # 💾 Genererede data (ignoreret af git)
│   └── housing.duckdb         # Lokal database (auto-genereret)
│
├── logs/                       # 📝 Applikations logs (ignoreret af git)
├── docs/                       # 📚 Teknisk dokumentation
└── venv/                       # 🐍 Python virtuelt miljø
```

### 🎯 Hovedkommandoer:
- **`python3 start.py full`** - Kør pipeline + start webapp (anbefalet første gang)
- **`python3 start.py pipeline`** - Kør kun data pipeline
- **`python3 start.py app`** - Start kun webapp
- **`python3 start.py scheduler`** - Start automatiseret scheduler
- **`python3 start.py setup`** - Kun opsætning af miljø

## 📚 Teknisk Dokumentation

- [`docs/extraction-update-log.md`](docs/extraction-update-log.md): Detaljeret log over opdateringer til data extraction
- [`docs/boliga-api-documentation.md`](docs/boliga-api-documentation.md): Komplet dokumentation af boliga.dk's API struktur
- [`docs/enhanced-scoring-algorithm.md`](docs/enhanced-scoring-algorithm.md): Detaljeret dokumentation af den forbedrede scoring algoritme

## 🏃‍♂️ Kørsel af Systemet

### 🎯 Integreret Startup Script (ANBEFALET)
Brug `start.py` scriptet til alle operationer med automatisk miljø-opsætning:

**Første gang eller frisk opsætning - automatisk opsætning + kør pipeline + start webapp:**
```bash
python3 start.py full
```

**Kun opsætning af miljøet (virtuelt miljø + dependencies):**
```bash
python3 start.py setup
```

**Kør kun data pipeline (med auto-opsætning):**
```bash
python3 start.py pipeline
```

**Start kun webapp (med auto-opsætning):**
```bash
python3 start.py app
```

**Start automatiseret scheduler (med auto-opsætning):**
```bash
python3 start.py scheduler
```

**Spring automatisk opsætning over og brug system Python:**
```bash
python3 start.py pipeline --skip-setup
```

### 📖 Detaljerede Kommandoer

#### 1. Manuel Pipeline Kørsel
Udtræk og proces boligdata én gang:
```bash
python start.py pipeline
# ELLER direkte:
python pipeline/run_pipeline.py
```

#### 2. Kør Web Appen
Start Streamlit appen til at browse boligdata:
```bash
python start.py app
# ELLER direkte:
streamlit run app/app_local.py
```
Appen vil være tilgængelig på http://localhost:8501

#### 3. Planlagte Automatiske Kørsler
Opsæt automatisk dataindsamling:

**Kør automatiseret scheduler:**
```bash
python start.py scheduler
# ELLER direkte:
python scripts/scheduler.py
```

**Start scheduleren (kører dagligt kl. 6 + hver 4. time i aktive timer):**
```bash
python scheduler.py
```

## 🏗️ Arkitektur og Filstruktur

### Data Pipeline
1. **Extract** (`src/extract_listings_local.py`): Scraper boliga.dk for postnumre omkring Aarhus
2. **Transform** (`src/transform_listings_local.py`): Beregner score baseret på byggeår, pris, størrelse, værelser og dage på markedet
3. **App** (`app/app_local.py`): Streamlit webapp til browsing og marking af sete huse
4. **Database** (`src/database_local.py`): DuckDB database management
5. **Scheduler** (`scripts/scheduler.py`): Automated daily pipeline execution
6. **Pipeline Runner** (`pipeline/run_pipeline.py`): Main pipeline orchestration

### Teknologi Stack
- **Database**: DuckDB (let og hurtig lokal database)
- **Processing**: Pandas (dataframe processing)
- **Scheduling**: APScheduler (Python scheduling)
- **Frontend**: Streamlit (lokal webapp)
- **Environment**: Python virtual environment

### Arkitektur Migration

**Fra Databricks:**
- ✅ Databricks Delta Lake → DuckDB
- ✅ PySpark DataFrame → Pandas DataFrame  
- ✅ Databricks SQL → DuckDB SQL
- ✅ Databricks Apps → Lokal Streamlit
- ✅ Databricks Jobs → APScheduler

**Fordele ved Lokal Opsætning:**
- Ingen cloud-omkostninger
- Fuld datakontrol
- Hurtigere udviklings-iteration
- Ingen internet-afhængighed for app-brug
- Simpel backup og gendannelse

## 💾 Database

Systemet bruger DuckDB, en hurtig analytisk database der gemmer data i en enkelt fil:
- **Lokation:** `data/housing.duckdb`
- **Tabeller:**
  - `listings`: Rå scraped data
  - `listings_scored`: Processerede data med scores
  - `seen_houses`: Bruger-markerede huse

## 📊 Forbedret Scoring Algoritme

Den forbedrede 8-faktor scoring system (max 80 point):

1. **Energiklasse** (0-10 point): A=10, B=8, C=6, D=4, E=2, F=0, Ukendt=3
2. **Tog Afstand** (0-10 point): GPS afstand til nærmeste tog/letbane
3. **Grundstørrelse** (0-10 point): Relativt til andre huse i samme postnummer
4. **Husstørrelse** (0-10 point): Relativt til andre huse i samme postnummer  
5. **Pris Effektivitet** (0-10 point): Pris/m² relativt til samme postnummer
6. **Byggeår** (0-10 point): Relativt til andre huse i samme postnummer
7. **Kælderstørrelse** (0-10 point): Relativt til andre huse i samme postnummer
8. **Dage på Marked** (0-10 point): Relativt til andre huse i samme postnummer

## 📊 Monitering

Tjek logs for systemets sundhed:
```bash
# Pipeline logs
tail -f logs/housing_pipeline.log

# Scheduler logs  
tail -f logs/scheduler.log
```

## 🛠️ Fejlfinding

**Ingen data i appen:**
1. Kør pipeline manuelt: `python start.py pipeline`
2. Tjek logs for fejl
3. Verificer internetforbindelse

**Database problemer:**
1. Slet `data/housing.duckdb` for at nulstille
2. Kør pipeline igen for at genopbygge data

**Streamlit fejl:**
1. Genstart appen: `Ctrl+C` derefter `python start.py app`
2. Tjek om pipeline er kørt succesfuldt

**Energimærke håndtering**: 
- Boliga.dk har mærkelige værdier som G,H,I,J,K,L der faktisk er A-klasse
- '-' eller manglende værdier bliver til UKENDT (3 point)
- Alle værdier normaliseres til store bogstaver