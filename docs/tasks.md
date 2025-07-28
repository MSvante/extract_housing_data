# Detaljerede Development Tasks

## 📋 Oversigt
Denne fil indeholder detaljerede implementeringsopgaver baseret på `next-step.md` punkterne. Hver task er designet til at være konkret og actionable.

---

## 1. 🎛️ Konfigurerbar Vægtning og Dynamisk Scoring

### 1.1 Refaktorer Transform Pipeline
**Beskrivelse**: Omstrukturér så individual score-komponenter beregnes i transform, men final vægtning sker i front-end.

**Nuværende parametre (alle beregnes som 0-10 point)**:
- Energiklasse (global)
- Togstation afstand (global) 
- Grundstørrelse (relativ per postnummer)
- Husstørrelse (relativ per postnummer)
- Priseffektivitet (relativ per postnummer)
- Byggeår (relativ per postnummer)
- Kælderstørrelse (relativ per postnummer)
- Dage på marked (relativ per postnummer)

**Tasks**:
- [x] Fjern `total_score` beregning fra `transform_listings_local.py`
- [x] Behold kun individuelle score komponenter (score_energy, score_train_distance, etc.)
- [x] Fjern `total_score` kolonne fra database schema
- [x] Test at alle individuelle scores stadig beregnes korrekt

### 1.2 Front-end Vægtnings System
**Beskrivelse**: Implementer dynamisk vægtning og score beregning i Streamlit app.

**Tasks**:
- [x] Lav `DynamicScoringEngine` klasse i `src/dynamic_scoring.py`
- [x] Implementer real-time score beregning: `total_score = sum(individual_score * weight/100)`
- [x] Standard vægtning: 12.5% per parameter (100% / 8 = 12.5%)
- [x] Implementer vægtnings validering (sum skal være 100%)
- [x] Cache beregnede scores for performance når weights ikke ændres

### 1.3 Vægtnings UI i Streamlit
**Beskrivelse**: Lav brugervenlig interface til at justere vægtninger med manual trigger.

**Tasks**:
- [x] Tilføj vægtnings sektion i sidebar OVER filtere
- [x] Implementer sliders for hver parameter (0-100%)
- [x] Real-time validering og normalisering af vægte (kun UI feedback)
- [x] Vis total vægtning (skal være 100%) med color coding
- [x] Auto-justér andre vægte når én ændres (optional behavior)
- [x] Tilføj "🔄 Genberegn Scores" knap som trigger re-scoring
- [x] Disable/enable knap baseret på om vægte har ændret sig

### 1.4 Foruddefinerede Profiler
**Beskrivelse**: Lav foruddefinerede vægtnings-profiler for forskellige brugertyper.

**Profiler**:
- **"Standard (lige vægt)"**: Alle 12.5%
- **"Familievenlig"**: Husstørrelse 20%, Grundstørrelse 20%, Byggeår 15%, Energi 15%, Kælder 10%, Transport 10%, Pris 5%, Marked 5%
- **"Investering"**: Priseffektivitet 25%, Dage på marked 20%, Transport 15%, Energi 15%, Husstørrelse 10%, Byggeår 10%, Grundstørrelse 3%, Kælder 2%
- **"Førstegangskøber"**: Priseffektivitet 30%, Energi 20%, Transport 15%, Husstørrelse 15%, Byggeår 10%, Marked 5%, Grundstørrelse 3%, Kælder 2%
- **"Pensionist"**: Energi 25%, Transport 20%, Byggeår 15%, Husstørrelse 15%, Priseffektivitet 10%, Marked 10%, Grundstørrelse 3%, Kælder 2%
- **"Miljøbevidst"**: Energi 35%, Transport 25%, Byggeår 15%, Priseffektivitet 10%, Husstørrelse 8%, Marked 4%, Grundstørrelse 2%, Kælder 1%

**Tasks**:
- [x] Definer profiler som dict i `DynamicScoringEngine`
- [x] Lav profil dropdown OVER vægtnings sliders
- [x] Auto-opdater sliders når profil vælges
- [x] Tilføj "Custom" profil når user ændrer vægte manuelt
- [x] Vis aktiv profil navn

### 1.5 Performance Optimering
**Beskrivelse**: Sørg for at score beregning er effektiv når triggered manuelt.

**Tasks**:
- [x] Cache score beregninger baseret på weight signature
- [x] Vis loading spinner under score genberegning
- [x] Vis progress bar ved store datasets
- [x] Optimer pandas operations for score calculation
- [x] Implementer state management så kun ændrede vægte trigger genberegning

---

## 2. 💰 Månedlige Ejerudgifter Integration

### 2.1 Research og Data Vurdering
**Beskrivelse**: Undersøg om månedlige ejerudgifter data er tilgængelig fra boliga.dk eller andre kilder.

**Tasks**:
- [ ] Analysér boliga.dk JSON response for ejerudgifts-felter
- [ ] Research alternative datakilder (ejendomsdata.dk, tinglysning.dk)
- [ ] Test scraping af ekstra data hvis nødvendigt
- [ ] Dokumenter findings i `docs/ejerudgifter-research.md`

### 2.2 Ejerudgifts Estimering (hvis data ikke tilgængelig)
**Beskrivelse**: Implementer estimering baseret på hustype, størrelse og postnummer.

**Estimering komponenter**:
- Ejendomsværdiskat (ca. 1% af ejendomsværdi)
- Grundskyld (varierer per kommune)
- Forsikring (estimat baseret på husværdi)
- Vedligeholdelse (estimat baseret på alder og størrelse)

**Tasks**:
- [ ] Lav `MonthlyExpenseCalculator` klasse
- [ ] Implementer estimering algoritmer
- [ ] Integrér i transform pipeline
- [ ] Tilføj månedlige udgifter som ny scoring parameter (0-10 point)

---

## 3. 🗺️ Interaktivt Kort Funktionalitet

### 3.1 Kort Implementation
**Beskrivelse**: Tilføj interaktivt kort med housing data visualization.

**Tasks**:
- [ ] Installér Folium eller Plotly mapping library
- [ ] Lav `MapVisualization` klasse i `src/map_utils.py`
- [ ] Implementer basis kort med zoom og pan
- [ ] Plot huse som markører med color-coding efter score
- [ ] Implementer clustering for bedre performance ved mange huse

### 3.2 Hover Popup Data
**Beskrivelse**: Vis bolig information når man hover over kort markører.

**Popup indhold**:
- Adresse
- Samlet pris (formateret)
- m² størrelse
- Total score
- Top 3 score faktorer

**Tasks**:
- [ ] Design popup HTML template
- [ ] Implementer hover event handling
- [ ] Formatér tal og tekst brugervenligt
- [ ] Test på forskellige skærm størrelser

### 3.3 Kort Integration i App
**Beskrivelse**: Tilføj kort som ny tab i Streamlit app.

**Tasks**:
- [ ] Lav ny "🗺️ Kort" tab i `app_local.py`
- [ ] Syncronisér kort filtre med main app filtre
- [ ] Implementer bidirektional opdatering (kort ↔ tabel)
- [ ] Optimér performance for store datasæt

---

## 4. 📡 Ekstern Data Integration

### 4.1 Rejseplanen API Integration (Primær transport data)
**Beskrivelse**: Implementer integration med Rejseplanen API for komplet offentlig transport data.

**Tasks**:
- [ ] Opsæt Rejseplanen API adgang (https://help.rejseplanen.dk/hc/da/articles/214174465-Rejseplanens-API)
- [ ] Lav `RejseplanenEnricher` klasse i `src/external_data.py`
- [ ] Implementer søgning efter stationer/stoppesteder inden for radius
- [ ] Beregn transport score baseret på: antal stoppesteder, transport typer (S-tog vs bus), frekvens
- [ ] Tilføj data caching i DuckDB for at respektere rate limits
- [ ] Håndter forskellige transport typer: S-tog (høj score), Metro (høj score), Bus (medium score)

### 4.2 OpenStreetMap Integration (Supplerende POI data)
**Beskrivelse**: Brug OSM for POI data hvor Rejseplanen ikke dækker.

**Tasks**:
- [ ] Installér `overpy` library for OSM Overpass API  
- [ ] Implementer `OSMEnricher` klasse i `src/external_data.py`
- [ ] Fokusér på non-transport POI: supermarkeder, apotek, skoler, banker
- [ ] Implementer service score (facility density inden for 2km radius)
- [ ] Kategorisér POI typer og vægt dem forskelligt
- [ ] Cache OSM data lokalt med intelligent refresh strategi

### 4.3 Danmarks Statistik Integration (Fase 2)
**Beskrivelse**: Tilføj demografisk scoring baseret på postnummer data.

**Tasks**:
- [ ] Research DST API endpoints for relevante data
- [ ] Implementer `DemographicsEnricher` klasse i `src/external_data.py`
- [ ] Hent indkomst, uddannelsesniveau, aldersfordeling per postnummer
- [ ] Design demografisk score algoritme
- [ ] Cache demografisk data lokalt (opdateres sjældent)

### 4.4 Ny Scoring Parametre
**Beskrivelse**: Integrér eksterne data som nye scoring faktorer.

**Nye parametre (0-10 point hver)**:
- Rejseplanen transport score (erstatter nuværende tog-distance score)
- Service/indkøb density score (OSM data)
- Demografisk match score (DST data)
- Miljøkvalitet score (hvis tilgængelig)

**Tasks**:
- [ ] Udvid `transform_listings_local.py` med nye scores
- [ ] Opdater vægtnings system til at håndtere 10+ parametre  
- [ ] Erstat nuværende `score_train_distance` med `score_transport_access`
- [ ] Opdater app visning med nye score kolonner
- [ ] Tilføj nye filer til `start.py` script dependency check

---

## 5. 🔮 What-if Scenarier

### 5.1 Scenarie Engine
**Beskrivelse**: Implementer system til at lave "hvad hvis" analyser på bolig data.

**Tasks**:
- [ ] Lav `ScenarioEngine` klasse i `src/scenario_analysis.py`
- [ ] Implementer parameter modification (pris, størrelse, byggeår, etc.)
- [ ] Berregn ændret score baseret på modifications
- [ ] Support for både absolutte ændringer og procentvise ændringer

### 5.2 Foruddefinerede Scenarier
**Beskrivelse**: Lav common scenarier som brugere kan vælge imellem.

**Scenarier**:
- "Prisfald 10%" - reducér pris med 10%
- "Energirenovering" - opgrader energiklasse med 1 niveau
- "Kælder tilbygning" - tilføj 50m² kælder
- "Markedstid 50% mindre" - halvér dage på marked
- "Transport forbedring" - simuler ny letbane station 2km væk

**Tasks**:
- [ ] Definer scenarier som konfiguration
- [ ] Implementer scenarie selector i Streamlit
- [ ] Vis original vs modificeret score side om side
- [ ] Highlight hvilke factors der ændres mest

### 5.3 Custom Scenarie Builder
**Beskrivelse**: Lad brugere lave deres egne what-if scenarier.

**Tasks**:
- [ ] Lav interaktiv scenarie builder i Streamlit
- [ ] Support for multi-parameter ændringer
- [ ] Tilføj "🔄 Beregn Scenarie" knap til at trigger beregning
- [ ] Gem og del scenarier mellem sessioner

---

## 6. ⭐ Favoritter System

### 6.1 Database Schema Udvidelse
**Beskrivelse**: Udvid database til at støtte favoritter med noter.

**Tasks**:
- [ ] Lav `favorites` tabel i `database_local.py`:
  ```sql
  CREATE TABLE favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ouId INTEGER REFERENCES listings_scored(ouId),
      added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      notes TEXT,
      user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
      tags VARCHAR  -- komma-separeret liste
  );
  ```
- [ ] Implementer CRUD operations for favoritter
- [ ] Håndter data persistence ved pipeline re-runs

### 6.2 Favorit Management UI
**Beskrivelse**: Tilføj favorit funktionalitet til Streamlit app.

**Tasks**:
- [ ] Tilføj "Tilføj til favoritter" knap i bolig listings
- [ ] Lav ny "⭐ Favoritter" tab
- [ ] Implementer notes editor og rating system
- [ ] Tilføj tag system til kategorisering
- [ ] Vis favoritter uagtet af aktive filtre

### 6.3 PDF Export
**Beskrivelse**: Lav PDF rapport af favoritter.

**Tasks**:
- [ ] Installér `reportlab` eller `weasyprint` for PDF generation
- [ ] Design PDF template med bolig data og billeder
- [ ] Implementer export funktionalitet
- [ ] Inkluder notes, ratings og personlige kommentarer
- [ ] Tilføj "Eksportér til PDF" knap i favoritter tab

---

## 7. 📊 Postnummer Statistikker

### 7.1 Statistik Beregning
**Beskrivelse**: Berregn omfattende statistikker per postnummer.

**Statistikker**:
- Gennemsnitspris og median pris
- Gennemsnit m² pris
- Antal aktive listings
- Gennemsnit tid på marked
- Score distribution (min, max, average per parameter)
- Grundstørrelse statistics
- Byggeår distribution

**Tasks**:
- [ ] Lav `PostcodeStatistics` klasse i `src/stats_calculator.py`
- [ ] Implementer alle statistik beregninger
- [ ] Cache statistikker for bedre performance
- [ ] Håndter postnumre med få listings

### 7.2 Sammenligning På Tværs
**Beskrivelse**: Lav værktøj til at sammenligne postnumre direkte.

**Tasks**:
- [ ] Lav ny "📊 Postnummer Stats" tab i app
- [ ] Implementer multi-select for postnummer sammenligning
- [ ] Vis side-om-side comparison tabel
- [ ] Tilføj visualiseringer (bar charts, radar charts)
- [ ] Highlight største forskelle mellem områder

### 7.3 Trend Visualisering
**Beskrivelse**: Vis udvikling og trends i postnummer data.

**Tasks**:
- [ ] Implementer time-series data collection
- [ ] Lav trend charts for pris udvikling
- [ ] Vis market activity trends (antal nye listings per uge)
- [ ] Sammenlign score trends mellem postnumre

---

## 8. 🏆 Topscorer Funktionalitet

### 8.1 Kategori Topscorer
**Beskrivelse**: Vis top 1 hus per scoring kategori som HTML cards på forsiden.

**Kategorier**:
- Bedste samlet score
- Billigste per m²
- Største hus
- Nyeste byggeår
- Bedste energiklasse
- Størst grund
- Tættest på transport
- Hurtigst salg (færrest dage på marked)

**Tasks**:
- [ ] Lav `TopScorerCalculator` klasse i `src/top_scorers.py`
- [ ] Implementer kategori-baseret ranking
- [ ] Håndter ties og edge cases
- [ ] Integrér som HTML cards på main page (ikke separat tab)

### 8.2 Topscorer Visning på Forsiden
**Beskrivelse**: Elegant præsentation af topscorer data som cards på main page.

**Tasks**:
- [ ] Design compact HTML cards layout (4 cards per række)
- [ ] Vis thumbnail billede (første image fra image_urls)
- [ ] Highlight den vindende metric med farve/ikon
- [ ] Tilføj click-to-expand funktionalitet
- [ ] Placér cards OVER filter sektion på main page
- [ ] Tilføj "Tilføj til favoritter" knap direkte på card

### 8.3 Dynamisk Filtering
**Beskrivelse**: Topscorere opdateres baseret på aktuelle filtre.

**Tasks**:
- [ ] Integrér topscorer med filter system
- [ ] Opdatering når filtre ændres eller "Genberegn" klikkes
- [ ] Vis "Ingen data" meddelelse hvis ingen matches i kategori
- [ ] Optimér performance ved store datasets
- [ ] Tilføj expand/collapse funktionalitet for topscorer sektion

---

## 🗒️ UI Ændringer (Implementeret)

### Ændringer 28/7/2025:
- [x] Flyttet checkbox filtre (postnummer match og sete huse) til bunden af sidebar
- [x] Ændret "Scoring Vægtning" til "Vægtning af parametre"
- [x] Fjernet "Aktuelle vægte" sektion fra vægtnings UI
- [x] Fjernet "Lokal Version" fra hovedtitel
- [x] Fjernet "Allerede sete huse" tab (tilføjes igen senere)
- [x] Fjernet "Markér huse som sete" sektion fra hovedside
- [x] Tilføjet titel "🏠 Alle Boliger" til hovedtabel

**Note**: "Allerede sete huse" tab skal genimplementeres senere som del af opgave 12.

---

## 12. 👁️ Forbedret "Set" Huse System

### 12.1 Database Schema Forbedring
**Beskrivelse**: Forbedre seen_houses tabel struktur og funktionalitet.

**Nuværende problemer med seen_houses**:
- Mangler timestamps og metadata
- Ingen batch operations
- Ikke optimeret til frequent queries

**Tasks**:
- [ ] Redesign `seen_houses` tabel i `database_local.py`:
  ```sql
  CREATE TABLE seen_listings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ouId INTEGER NOT NULL,
      marked_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      notes TEXT,
      user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
      is_hidden BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  CREATE INDEX idx_seen_listings_ouid ON seen_listings(ouId);
  CREATE INDEX idx_seen_listings_hidden ON seen_listings(is_hidden);
  ```
- [ ] Implementer migration fra old seen_houses tabel
- [ ] Tilføj CRUD operations med batch support

### 12.2 Forbedret UI Integration  
**Beskrivelse**: Forbedre hvordan "set" huse håndteres i app interface.

**Tasks**:
- [ ] Tilføj "Marker som set" checkbox ved hver bolig i listen
- [ ] Implementer batch "Marker valgte som set" funktionalitet
- [ ] Forbedre filter checkbox: "Skjul sete huse" (standard: checked)
- [ ] Tilføj hurtig "Marker alle som set" knap ved bund af listen
- [ ] Vis "Set" status visuelt i bolig listings (fx grå baggrund)

### 12.3 Set Huse Management
**Beskrivelse**: Lav administration af sete huse.

**Tasks**:
- [ ] Forbedre "🔍 Sete huse" tab med bedre functionality
- [ ] Tilføj batch "Fjern fra sete" operation  
- [ ] Implementer search/filter i sete huse
- [ ] Tilføj notes og rating til sete huse
- [ ] Export sete huse til CSV/PDF
- [ ] Vis statistikker: "Du har set X huse de sidste Y dage"

---

## 9. 🔍 Lignende Huse Funktionalitet

### 9.1 Similarity Algorithm
**Beskrivelse**: Definer og implementér algoritme til at finde lignende huse.

**Similarity faktorer (lige vægt)**:
- Pris per m² afvigelse (±20% = høj similarity)
- Byggeår afvigelse (±10 år = høj similarity)  
- Grundstørrelse afvigelse (±30% = høj similarity)

**Similarity beregning**:
```
similarity_score = (
    (1 - abs(house1_m2_price - house2_m2_price) / max(house1_m2_price, house2_m2_price)) * 33.33 +
    (1 - abs(house1_build_year - house2_build_year) / 50) * 33.33 +
    (1 - abs(house1_lot_size - house2_lot_size) / max(house1_lot_size, house2_lot_size)) * 33.33
)
```

**Tasks**:
- [ ] Lav `SimilarityCalculator` klasse i `src/similarity_finder.py`
- [ ] Implementer similarity scoring algoritme
- [ ] Set minimum similarity threshold (fx 70%)
- [ ] Optimér for performance med store datasets

### 9.2 Cross-Postcode Search
**Beskrivelse**: Find lignende huse på tværs af postnumre.

**Tasks**:
- [ ] Implementer cross-postcode similarity search
- [ ] Vis similarity score som procentuel match
- [ ] Sortér efter similarity score (højeste først)
- [ ] Tilføj "Lignende huse" sektion til bolig detail view
- [ ] Limit til top 5-10 mest lignende huse

### 9.3 Similarity Insights
**Beskrivelse**: Giv indsigt i hvorfor huse er lignende.

**Tasks**:
- [ ] Vis breakdown af similarity faktorer
- [ ] Highlight hvilke metrics der matcher bedst
- [ ] Sammenlign side-om-side med original hus
- [ ] Tilføj "Hvorfor er dette lignende?" explanation

---

## 10. 📈 Indbyggede Benchmarks

### 10.1 Postnummer Benchmarks
**Beskrivelse**: Sammenlign hver bolig med gennemsnittet i postnummeret.

**Sammenligninger**:
- "Dette hus er 12% billigere end gennemsnittet i området"
- "Prisen per m² er 8% højere end lokalområdet"
- "Grundstørrelsen er 45% større end normalt for postnummeret"
- "Byggeåret er 15 år nyere end gennemsnittet"

**Tasks**:
- [ ] Lav `BenchmarkCalculator` klasse i `src/benchmarks.py`
- [ ] Berregn postnummer gennemsnit for alle metrics
- [ ] Implementer procentuelle afvigelser
- [ ] Håndter edge cases (fx kun ét hus i postnummer)

### 10.2 Benchmark Visning
**Beskrivelse**: Elegant visning af benchmark data i app.

**Tasks**:
- [ ] Tilføj benchmark kolonne til bolig listings
- [ ] Implementer hover tooltips med detaljerede benchmarks
- [ ] Farv-kod positive/negative afvigelser (grøn/rød)
- [ ] Lav expandable benchmark sektion per bolig

### 10.3 Benchmark Insights
**Beskrivelse**: Giv dybere indsigt i benchmark data.

**Tasks**:
- [ ] Lav "📈 Benchmark Analyse" tab
- [ ] Vis distribution af værdier i postnummer
- [ ] Highlight outliers og exceptionally good deals
- [ ] Tilføj "Deal Score" baseret på hvor mange benchmarks der er positive

---

## 11. 🔧 Address Display Refactor ✅

### 11.1 Fjern Full Address Creation ✅
**Beskrivelse**: Opdater transform script til at ikke lave full address string.

**Tasks**:
- [x] Fjern `# Create full address` sektion fra `transform_listings_local.py` linje 134
- [x] Remove `full_address` fra column selection
- [x] Update database schema til at fjerne `full_address` felt hvis nødvendigt
- [x] Ensure `address_text`, `house_number`, og `city` er individuelle kolonner

### 11.2 App Display Update ✅
**Beskrivelse**: Vis adresse og by som separate kolonner i Streamlit app.

**Tasks**:
- [x] Opdater `app_local.py` til at bruge separate adresse kolonner
- [x] Lav address display som: `{address_text} {house_number}`
- [x] Vis by som separat kolonne
- [x] Update alle steder hvor `full_address` bruges

### 11.3 Clickable Address Implementation ✅
**Beskrivelse**: Gør adresser clickable og åbner Google søgning.

**Funktionalitet**:
- Click på adresse → åbner ny browser tab
- Google søgning: `"[address] [city] boliga site:boliga.dk"`
- Dette finder typisk mægler opslag på boliga.dk

**Tasks**:
- [x] Implementer clickable address links i Streamlit
- [x] Format Google søge URL korrekt
- [x] Test at søgningen finder relevante sider
- [x] Overvej alternative søge strategier (direct boliga.dk link via ouId)

**Alternative implementation**:
- Direct link til boliga.dk via ouId: `https://www.boliga.dk/bolig/[ouId]`
- Kan være mere direkte end Google søgning

**Tasks for alternative**:
- [x] Test direct boliga.dk URL pattern
- [x] Implementer hvis URL pattern er stabil
- [x] Fallback til Google søgning hvis direct link fejler

---

## 📅 Implementation Timeline

### Sprint 1 (2 uger)
- Task 11: Address refactor ✅
- Task 1.1-1.3: Vægtnings system (nye filer: `src/dynamic_scoring.py`) ✅
- Task 12.1-12.2: Forbedret seen houses system
- Task 8.1-8.2: Topscorer cards på forside (ny fil: `src/top_scorers.py`) ✅

### Sprint 2 (2 uger)  
- Task 3: Kort funktionalitet (ny fil: `src/map_utils.py`)
- Task 10: Benchmark system (ny fil: `src/benchmarks.py`) 
- Task 6.1-6.2: Favoritter basic functionality

### Sprint 3 (3 uger)
- Task 4.1-4.2: Rejseplanen + OSM integration (filer: `src/external_data.py`)
- Task 7: Postnummer statistikker (ny fil: `src/stats_calculator.py`)
- Task 9: Lignende huse (ny fil: `src/similarity_finder.py`)

### Sprint 4 (2 uger)
- Task 5: What-if scenarier (ny fil: `src/scenario_analysis.py`)
- Task 2: Månedlige ejerudgifter
- Task 6.3: PDF export
- Task 12.3: Advanced seen houses management

### Sprint 5 (1 uge)
- Task 4.3-4.4: Danmarks Statistik integration
- Testing og optimering
- start.py script updates for nye filer
- Dokumentation

### 📁 Nye Filer der skal tilføjes til start.py dependency check:
```python
REQUIRED_SRC_FILES = [
    'src/extract_listings_local.py',
    'src/transform_listings_local.py', 
    'src/database_local.py',
    'src/dynamic_scoring.py',        # Task 1
    'src/external_data.py',          # Task 4
    'src/map_utils.py',              # Task 3
    'src/top_scorers.py',            # Task 8
    'src/stats_calculator.py',       # Task 7
    'src/similarity_finder.py',      # Task 9
    'src/scenario_analysis.py',      # Task 5
    'src/benchmarks.py'              # Task 10
]
```

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] Test scoring algorithms med mock data
- [ ] Test external API integration med stub responses
- [ ] Test database operations
- [ ] Test vægtnings calculations

### Integration Tests
- [ ] End-to-end pipeline test
- [ ] Streamlit app functionality test
- [ ] Database persistence test
- [ ] External API rate limiting test

### Performance Tests
- [ ] Large dataset handling (1000+ listings)
- [ ] External API response times
- [ ] Map rendering performance
- [ ] Database query optimization

---

## 📋 Definition of Done

For hver task gælder:
- [ ] Feature er implementeret og testet
- [ ] Code er dokumenteret med docstrings
- [ ] Unit tests skrevet og passerer
- [ ] Integration med eksisterende system verificeret
- [ ] Performance er acceptable (< 5 sek response time)
- [ ] Error handling implementeret
- [ ] User interface er intuitivt og brugervenligt
- [ ] Feature er dokumenteret i README eller relevante docs

---

## 🔄 Maintenance og Overvejelser

### Kontinuerlig forbedring
- Monitor external API stability og data quality
- User feedback integration
- Performance optimization baseret på usage patterns
- Ny externe datakilder når de bliver tilgængelige

### Teknisk gæld håndtering
- Regular code reviews
- Refactoring af komplekse komponenter
- Database optimization ved øget data volume
- Error monitoring og logging forbedringer
