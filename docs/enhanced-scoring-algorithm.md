# Forbedret Scoring Algoritme Dokumentation

## Oversigt

Den forbedrede scoring algoritme evaluerer ejendomme baseret på 8 faktorer med lige vægtning, der giver en maksimal score på 80 point. Alle faktorer undtagen energiklasse og tog-afstand scores relativt til andre ejendomme inden for samme postnummer.

## Scoring Metode

### Global Scoring (2 faktorer)
Anvendes konsistent på tværs af alle postnumre:
- **Energiklasse**: Universelle energieffektivitetsstandarder
- **Tog Afstand**: Geografisk nærhed til offentlig transport

### Relativ Scoring (6 faktorer) 
Rangeret inden for hvert postnummer ved hjælp af tæt rangering:
- **Byggeår**: Sammenlignet med andre huse i samme postnummer
- **Husstørrelse**: Relativt til lokalt marked
- **Pris Effektivitet**: Sammenlignet med lokale pris/m² værdier
- **Grundstørrelse**: Relativt til lokale grundstørrelser
- **Kælderstørrelse**: Sammenlignet med lokale kælderstørrelser  
- **Dage på Marked**: Relativt til lokal markedstiming

## Scoring Faktorer (Alle 10 point max undtagen angivet)

### 1. Energiklasse Score (Global)
- **A**: 10 point
- **B**: 8 point  
- **C**: 6 point
- **D**: 4 point
- **E**: 2 point
- **F/G**: 0 point
- **Manglende/Ukendt**: 3 point (standard)

### 2. Tog Afstand Score (Global)
- Beregnet ved hjælp af Haversine formel til nærmeste togstation eller letbane stop
- Stationer inkluderet:
  - **Hovedstationer**: Aarhus H, Skanderborg St, Randers St, Hadsten St, Hinnerup St, Langå St
  - **Letbane**: Risskov, Skejby, Universitetshospitalet, Skejby Sygehus, Lisbjerg Skole, Lisbjerg Kirkeby, Lystrup, Ryomgård, Grenaa
- Score formel: `10 * (1 - afstand_km / 25)`
- Maksimal afstand betragtet: 25km
- Alle stationer har lige vægt (ingen stations-vægtning)

### 3. Byggeår Score (Relativ inden for postnummer)
- Bruger tæt rangering: nyeste hus i postnummer = 10 point, ældste = 0 point
- Lineær interpolation mellem rækker

### 4. Husstørrelse Score (Relativ inden for postnummer)
- Bruger tæt rangering: største hus i postnummer = 10 point, mindste = 0 point
- Baseret på m² gulvareal

### 5. Pris Effektivitet Score (Relativ inden for postnummer)
- Bruger tæt rangering baseret på pris per m²: billigste/m² i postnummer = 10 point, dyreste = 0 point
- Beregnet som: pris ÷ m² derefter rangeret

### 6. Grundstørrelse Score (Relativ inden for postnummer)
- Bruger tæt rangering: største grund i postnummer = 10 point, mindste = 0 point
- Baseret på grundstørrelse i m²

### 7. Kælderstørrelse Score (10 point max, Relativ inden for postnummer)
- Bruger tæt rangering: største kælder i postnummer = 10 point, mindste = 0 point
- Baseret på kælderstørrelse i m²

### 8. Dage på Marked Score (Relativ inden for postnummer)
- Bruger tæt rangering: færrest dage i postnummer = 10 point, flest dage = 0 point
- Friskere opslag scorer højere

## Total Score Beregning

```
total_score = energi_score + 
              tog_afstand_score + 
              byggeår_score + 
              husstørrelse_score + 
              pris_effektivitet_score + 
              grundstørrelse_score + 
              kælder_score + 
              dage_marked_score
```

**Maksimal mulig score**: 80 point (8 × 10 point)

## Implementerings Detaljer

### Relativ Scoring Formel
For postnummer relative faktorer:
```
score = 10 * (rang - 1) / (max_rang - 1)
```
Hvor rang 1 = bedste værdi, max_rang = værste værdi i det postnummer.

### UDF Funktioner
- `calculate_distance_udf()`: Beregner togstations afstande ved hjælp af Haversine formel
- `energy_class_score_udf()`: Mapper energiklasser til scores med sikre fallbacks

### Fejlhåndtering
- Manglende GPS koordinater som standard til 0 point for tog afstand
- Manglende energiklasse som standard til 3 point
- Manglende grundstørrelse/kælderstørrelse som standard til 0
- Sikker type casting med fallbacks
- Enkelt hus i postnummer får 10 point for alle relative faktorer

### Performance Considerations
- Window functions partitioned by zip_code for relative scoring
- UDFs registered once per session
- Final score rounded to 2 decimal places

## Database Schema

The algorithm outputs these columns:
- `total_score`: Total points (0-80)
- `score_energy`: Energy class points (0-10)
- `score_train_distance`: Train proximity points (0-10)
- `score_build_year`: Build year points (0-10)
- `score_house_size`: House size points (0-10)
- `score_price_efficiency`: Price efficiency points (0-10)
- `score_lot_size`: Lot size points (0-10)
- `score_basement`: Basement points (0-10)
- `score_days_market`: Market timing points (0-10)

## Fordele ved Denne Tilgang

### Fair Sammenligning
- Huse konkurrerer inden for deres lokale markedskontekst
- Et 1960'er hus i Aarhus C bliver ikke straffet mod 2020'er huse i forstæder
- Pris effektivitet afspejler lokale markedsrealiteter

### Afbalanceret Scoring
- Alle faktorer har lige 10-point bidrag
- Ingen kunstig vægtning der kan skævvride resultater
- Enkelt og gennemsigtigt scoring system

### Markedsrelevant
- Relativ scoring afspejler hvad købere faktisk sammenligner
- Tager højde for postnummer karakteristika og markeds segmenter
- Energi og transport forbliver universelt sammenlignelige

## Ændringer fra Forrige Version

### Fjernede Elementer
- Vægtet scoring (alle faktorer er nu lige)
- Fast kategorisk scoring for de fleste faktorer
- Stations vægtning for tog nærhed

### Forbedrede Elementer
- Fuld postnummer relativ scoring for 6/8 faktorer
- Udvidet letbane stations dækning
- Kælder scoring øget til 10 point (fra 5)
- Tilføjet Langå station for nordlig dækning

### Tekniske Forbedringer
- Bedre fejlhåndtering for kanttilfælde
- Renere kode struktur med utils.py
- Mere omfattende stations dækning

## Database Schema

Den forbedrede algoritme udskriver disse kolonner:
- `total_score`: Vægtet total (0-80)
- `score_energy`: Energiklasse point (0-10)
- `score_train_distance`: Tog nærhed point (0-10)
- `score_lot_size`: Grundstørrelse point (0-10)
- `score_house_size`: Husstørrelse point (0-10)
- `score_price_efficiency`: Pris effektivitet point (0-10)
- `score_build_year`: Byggeår point (0-10)
- `score_basement`: Kælder point (0-10)
- `score_days_market`: Markeds timing point (0-10)

## Test og Validering

Algoritmen er blevet valideret for at sikre:
- Alle scores falder inden for forventede områder
- UDF'er håndterer kant tilfælde elegant
- Performance er acceptabel for batch processing
- Resultater er reproducerbare og deterministiske

## Sammenfatning

Den forbedrede 8-faktor scoring algoritme giver et mere nuanceret og fair billede af boligers værdi ved at:
- Sammenligne boliger inden for deres lokale marked
- Prioritere både miljømæssige og praktiske faktorer
- Sikre alle faktorer har lige vægt i den endelige score
- Håndtere manglende data elegant med reasonable defaults
