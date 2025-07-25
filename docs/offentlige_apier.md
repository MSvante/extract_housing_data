# Offentlige API'er for Beriget Housing Data

## Oversigt
Denne fil dokumenterer research og vurdering af tilgængelige offentlige API'er, som kan berige vores housing data med ekstra information omkring skoler, transport, indkøb, aldersgruppering og andre relevante faktorer.

## 🚌 Transport og Mobilitet

### Rejseplanen API
- **URL**: https://help.rejseplanen.dk/hc/da/articles/214174465-Rejseplanens-API
- **Data**: Real-time offentlig transport, rutetider, stationer
- **Relevans**: Afstand til busstoppesteder, hyppighed af forbindelser
- **Format**: XML/JSON REST API
- **Begrænsninger**: Rate limits, kræver API nøgle
- **Scoring potentiale**: Transport score baseret på antal nærliggende stoppesteder og rute-frekvens

### OpenStreetMap Overpass API
- **URL**: https://overpass-api.de/
- **Data**: Vejdata, cykelstier, gå/cykel-infrastruktur
- **Relevans**: Walkability score, cykel-venlighed
- **Format**: JSON/XML
- **Begrænsninger**: Rate limits
- **Scoring potentiale**: Mobilitetsscore baseret på infrastruktur kvalitet

## 🏫 Uddannelse og Skoler

### Uddannelses- og Forskningsstyrelsen API
- **URL**: https://www.uvm.dk/aktuelt/nyheder/uvm/2020/maj/200522-nyt-api-giver-adgang-til-data-om-institutioner
- **Data**: Grundskoler, gymnasier, kvalitetsvurderinger
- **Relevans**: Afstand til gode skoler, skole ratings
- **Format**: JSON REST API
- **Begrænsninger**: Begrænset data tilgængelighed
- **Scoring potentiale**: Uddannelsesscore baseret på nærhed og kvalitet

### Kortforsyningen (Datafordeleren)
- **URL**: https://dataforsyningen.dk/
- **Data**: Skole lokationer, administrative grænser
- **Relevans**: Præcise skole-positioner
- **Format**: WFS/JSON
- **Begrænsninger**: Kræver registrering
- **Scoring potentiale**: Supplerer uddannelses API med geografisk data

## 🛒 Indkøb og Service

### Google Places API
- **URL**: https://developers.google.com/maps/documentation/places/web-service
- **Data**: Supermarkeder, butikker, restauranter, services
- **Relevans**: Nærhed til daglige indkøbsmuligheder
- **Format**: JSON REST API
- **Begrænsninger**: Betalings API, men generøs gratis quota
- **Scoring potentiale**: Service score baseret på tæthed af faciliteter

### OpenStreetMap Nominatim
- **URL**: https://nominatim.org/
- **Data**: POI (Points of Interest), butikker, faciliteter
- **Relevans**: Gratis alternativ til Google Places
- **Format**: JSON
- **Begrænsninger**: Mindre komplet end Google
- **Scoring potentiale**: Gratis service score

## 📊 Demografi og Socioøkonomi

### Danmarks Statistik API
- **URL**: https://www.dst.dk/da/Statistik/brug-statistikken/muligheder-i-statistikbanken/api
- **Data**: Befolkningsstatistik, indkomst, aldersfordeling, uddannelsesniveau
- **Relevans**: Socioøkonomisk profil af område
- **Format**: JSON REST API
- **Begrænsninger**: Kompleks API, data på postnummer/kommune niveau
- **Scoring potentiale**: Demografisk score baseret på områdets profil

### Geodata-styrelsen
- **URL**: https://dataforsyningen.dk/
- **Data**: Administrative enheder, befolkningsdata
- **Relevans**: Geografisk kobling af demografisk data
- **Format**: WFS/GeoJSON
- **Begrænsninger**: Kræver registrering
- **Scoring potentiale**: Supplement til DST data

## 🏥 Sundhed og Faciliteter

### Sundhedsdatastyrelsen
- **URL**: https://sundhedsdatastyrelsen.dk/da/afgoerelser-og-dokumenter/soegeresultater?query=api
- **Data**: Hospitaler, læger, tandlæger
- **Relevans**: Adgang til sundhedsfaciliteter
- **Format**: Begrænset offentlig API adgang
- **Begrænsninger**: Mest data ikke tilgængelig via API
- **Scoring potentiale**: Sundhedsscore hvis data tilgængelig

## 🌳 Miljø og Livskvalitet

### Miljøstyrelsen API
- **URL**: https://www.miljoeportal.dk/
- **Data**: Luftkvalitet, støjkort, forurening
- **Relevans**: Miljøkvalitet i området
- **Format**: Varierende
- **Begrænsninger**: Fragmenteret data
- **Scoring potentiale**: Miljøscore baseret på luft- og støjkvalitet

### Klimaatlas API
- **URL**: https://www.klimaatlas.dk/
- **Data**: Klimadata, oversvømmelsesrisiko
- **Relevans**: Klimarisiko vurdering
- **Format**: WMS/REST
- **Begrænsninger**: Primært visualisering, begrænset rå data
- **Scoring potentiale**: Klimarisiko score

## 🏃‍♀️ Rekreation og Sport

### OpenStreetMap (Parker og Sport)
- **URL**: https://overpass-api.de/
- **Data**: Parker, sportsanlæg, rekreative områder
- **Relevans**: Adgang til grønne områder og sport
- **Format**: JSON/XML via Overpass API
- **Begrænsninger**: Data kvalitet varierer
- **Scoring potentiale**: Rekreationsscore baseret på nærliggende faciliteter

## 🔒 Sikkerhed

### Politiets åbne data
- **URL**: https://www.politi.dk/om-politiet/organisation/nationale-specialer/national-cyber-og-informationssikkerhed-center-ncsc/aoabne-data
- **Data**: Begrænset kriminalitetsstatistik
- **Relevans**: Sikkerhed i området
- **Format**: CSV/Excel downloads
- **Begrænsninger**: Ikke real-time API, aggregeret data
- **Scoring potentiale**: Sikkerhedsscore hvis tilgængelig

## 📈 Anbefalet Implementerings-prioritet

### Fase 1 (Høj prioritet, let implementering)
1. **OpenStreetMap Overpass API** - Transport og POI data
2. **Google Places API** (begrænset gratis brug) - Butikker og service
3. **Rejseplanen API** - Offentlig transport

### Fase 2 (Medium prioritet)
1. **Danmarks Statistik API** - Demografisk data
2. **Kortforsyningen** - Skole data
3. **Miljøportal** - Miljødata hvis tilgængelig

### Fase 3 (Lavere prioritet, kompleks)
1. **Uddannelses API** - Skole kvalitet
2. **Sundhedsdata** - Hospital data
3. **Politidata** - Sikkerhedsstatistik

## 🔧 Teknisk Implementation

### API Integration Pattern
```python
class ExternalDataEnricher:
    def __init__(self):
        self.osm_client = OverpassClient()
        self.places_client = GooglePlacesClient()
        self.transport_client = RejseplanenClient()
    
    def enrich_listing(self, listing):
        lat, lon = listing['latitude'], listing['longitude']
        
        # Transport score
        transport_score = self.calculate_transport_score(lat, lon)
        
        # Service score  
        service_score = self.calculate_service_score(lat, lon)
        
        # Demographics score
        demo_score = self.calculate_demographics_score(listing['zip_code'])
        
        return {
            **listing,
            'transport_enriched_score': transport_score,
            'service_score': service_score, 
            'demographics_score': demo_score
        }
```

### Data Caching Strategy
- Cache API responses lokalt i DuckDB
- Refresh kun ved væsentlige ændringer
- Rate limit respekt gennem intelligent caching

## 📋 Næste Skridt
1. Test API adgang og data kvalitet for fase 1 API'er
2. Implementer grundlæggende OpenStreetMap integration
3. Design scoring algoritme for externe data
4. Implementer caching og rate limiting
5. Test med eksisterende housing data

## 🔍 Research Noter
- Mange danske offentlige API'er kræver registrering og/eller har begrænsninger
- OpenStreetMap er den mest tilgængelige kilde for geografisk POI data  
- Google Places giver højeste datakvalitet men har costs
- Danmarks Statistik API er komplekst men meget værdifuldt for demografisk scoring
- Mange miljø/sundhedsdata er ikke tilgængelige via strukturerede API'er
