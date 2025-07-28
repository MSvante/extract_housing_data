"""
Local Housing Data Streamlit App
Migrated from Databricks to work with local DuckDB
"""

import sys
from pathlib import Path
import streamlit as st

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from database_local import HousingDataDB
from dynamic_scoring import scoring_engine

st.set_page_config(layout="wide", page_title="🏠 Boligoversigt - Lokal Version")

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_listings_data():
    """Get listings data from local database."""
    db = HousingDataDB()
    try:
        listings_scored = db.get_listings_for_streamlit()
        return listings_scored
    finally:
        db.close()

@st.cache_data(ttl=30)
def get_seen_houses():
    """Get seen houses from local database."""
    db = HousingDataDB()
    try:
        seen_houses = db.get_seen_houses()
        return seen_houses
    finally:
        db.close()

def add_seen_house(ou_id: int):
    """Add house to seen list."""
    db = HousingDataDB()
    try:
        db.add_seen_house(ou_id)
    finally:
        db.close()

# Load data
try:
    listings_scored = get_listings_data()
    seen_houses = get_seen_houses()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if listings_scored.empty:
    st.warning("No data available. Please run the data pipeline first using `python run_pipeline.py`")
    st.stop()

# Main app content
st.title("🏠 Boligoversigt - Lokal Version")

# Initialize session state for weights early
if 'current_weights' not in st.session_state:
    st.session_state.current_weights = scoring_engine.DEFAULT_WEIGHTS.copy()
if 'selected_profile' not in st.session_state:
    st.session_state.selected_profile = 'Standard (lige vægt)'
if 'weights_changed' not in st.session_state:
    st.session_state.weights_changed = False

# ======== VÆGTNINGS SEKTION (Ekspanderbar på hovedsiden) ========
with st.expander("⚖️ **Scoring Vægtning**", expanded=False):
    # Create columns for better layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Profile selector
        profile_names = scoring_engine.get_profile_names()
        selected_profile = st.selectbox(
            "📋 Vælg profil:",
            profile_names,
            index=profile_names.index(st.session_state.selected_profile),
            key="main_profile_selector"
        )

        # Check if profile changed
        if selected_profile != st.session_state.selected_profile:
            st.session_state.selected_profile = selected_profile
            st.session_state.current_weights = scoring_engine.get_profile_weights(selected_profile)
            st.session_state.weights_changed = True

        st.write(f"**Aktiv profil:** {selected_profile}")
        
        # Show current weights summary
        st.write("**Aktuelle vægte:**")
        for param, display_name in scoring_engine.SCORE_PARAMETERS.items():
            weight = st.session_state.current_weights[param]
            st.write(f"• {display_name}: {weight:.1f}%")
    
    with col2:
        # Weight sliders
        st.write("**Juster vægtning (%):**")
        temp_weights = {}
        total_weight = 0

        # Create two columns for sliders
        slider_col1, slider_col2 = st.columns(2)
        params_list = list(scoring_engine.SCORE_PARAMETERS.items())
        mid_point = len(params_list) // 2
        
        with slider_col1:
            for param, display_name in params_list[:mid_point]:
                current_value = st.session_state.current_weights[param]
                new_value = st.slider(
                    f"{display_name}:",
                    min_value=0.0,
                    max_value=50.0,
                    value=current_value,
                    step=0.5,
                    key=f"main_weight_{param}"
                )
                temp_weights[param] = new_value
                total_weight += new_value
        
        with slider_col2:
            for param, display_name in params_list[mid_point:]:
                current_value = st.session_state.current_weights[param]
                new_value = st.slider(
                    f"{display_name}:",
                    min_value=0.0,
                    max_value=50.0,
                    value=current_value,
                    step=0.5,
                    key=f"main_weight_{param}"
                )
                temp_weights[param] = new_value
                total_weight += new_value

        # Show total weight with color coding
        if abs(total_weight - 100.0) < 0.1:
            st.success(f"✅ Total vægtning: {total_weight:.1f}%")
        elif total_weight > 100:
            st.error(f"❌ Total vægtning: {total_weight:.1f}% (for høj)")
        else:
            st.warning(f"⚠️ Total vægtning: {total_weight:.1f}% (for lav)")

        # Check if weights changed
        current_signature = str(sorted(st.session_state.current_weights.items()))
        temp_signature = str(sorted(temp_weights.items()))
        weights_changed_now = current_signature != temp_signature

        # Update session state
        if weights_changed_now:
            st.session_state.weights_changed = True
            # Auto-normalize if over 100%
            if total_weight > 100:
                temp_weights = scoring_engine.normalize_weights(temp_weights)

        # Recalculate scores button
        recalc_disabled = not st.session_state.weights_changed or abs(total_weight - 100.0) > 0.1
        if st.button("🔄 Genberegn Scores", disabled=recalc_disabled, type="primary", key="main_recalc_scores"):
            st.session_state.current_weights = temp_weights.copy()
            st.session_state.weights_changed = False
            scoring_engine.clear_cache()  # Clear cache to force recalculation
            st.rerun()

# ======== FILTER SEKTION ========
st.sidebar.title("🔍 **Filtrer Boliger**")

# Create filters on the right side of the screen
zip_codes = sorted(listings_scored['zip_code'].unique())
show_city_in_zip = st.sidebar.checkbox("Vis kun boliger med hvor bynavn er det samme som postnummeret", value=True)
show_already_seen_houses = st.sidebar.checkbox("Vis huse der allerede er markeret som set", value=False)
selected_zip_codes = st.sidebar.multiselect("Vælg postnumre", zip_codes, default=['8370','8382'])

# Enhanced filters
st.sidebar.subheader("📊 Basis Filtre")
max_budget = st.sidebar.number_input("Maksimalt budget", min_value=0, max_value=15000000, value=4000000, step=500000)
min_rooms = st.sidebar.number_input("Minimum antal værelser", min_value=0, max_value=15, value=5)
min_m2 = st.sidebar.number_input("Minimum m²", min_value=0, max_value=1000, value=150)
min_score = st.sidebar.number_input("Minimum samlet score", min_value=0, max_value=100, value=50, step=1)

# New enhanced filters
st.sidebar.subheader("🏗️ Boligdetaljer")
min_build_year = st.sidebar.number_input("Minimum byggeår", min_value=1800, max_value=2025, value=1960)
energy_classes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'UNKNOWN']
selected_energy_classes = st.sidebar.multiselect("Energiklasser", energy_classes, default=[])

min_lot_size = st.sidebar.number_input("Minimum grundstørrelse (m²)", min_value=0, max_value=5000, value=0)
min_basement_size = st.sidebar.number_input("Minimum kælderstørrelse (m²)", min_value=0, max_value=500, value=0)

# Join the seen_houses onto the listings_scored dataframe
if not seen_houses.empty:
    seen_houses['is_seen'] = True
    listings_scored = listings_scored.merge(seen_houses[['ouId', 'is_seen']], on='ouId', how='left')
    listings_scored['is_seen'] = listings_scored['is_seen'].fillna(False)
else:
    # If no seen houses, create the column with all False values
    listings_scored['is_seen'] = False

# Filter dataframe based on seen_houses
if not show_already_seen_houses:
    filtered_listings = listings_scored[~listings_scored['is_seen']]
else:
    filtered_listings = listings_scored      

# Apply dynamic scoring to filtered listings
filtered_listings = scoring_engine.apply_scoring(filtered_listings, st.session_state.current_weights)

# Apply all filters
# Only filter by zip codes if some are selected
if selected_zip_codes:
    filtered_listings = filtered_listings[filtered_listings['zip_code'].isin(selected_zip_codes)]

filtered_listings = filtered_listings[filtered_listings['price'] <= max_budget]
filtered_listings = filtered_listings[filtered_listings['rooms'] >= min_rooms]
filtered_listings = filtered_listings[filtered_listings['m2'] >= min_m2]
filtered_listings = filtered_listings[filtered_listings['dynamic_score'] >= min_score]

# Enhanced filters
filtered_listings = filtered_listings[filtered_listings['built'].astype(float) >= min_build_year]

# Energy class filter (handle missing values)
# Only apply energy class filter if some energy classes are selected
if selected_energy_classes:
    if 'UNKNOWN' in selected_energy_classes:
        # Include rows where energy_class is in selected classes OR is missing/null
        energy_filter = (filtered_listings['energy_class'].isin(selected_energy_classes)) | \
                       (filtered_listings['energy_class'].isna())
    else:
        # Only include rows where energy_class is in selected classes (exclude missing/null)
        energy_filter = filtered_listings['energy_class'].isin(selected_energy_classes)
    filtered_listings = filtered_listings[energy_filter]
# If no energy classes are selected, show all properties (no filter applied)

filtered_listings = filtered_listings[filtered_listings['lot_size'].fillna(0) >= min_lot_size]
filtered_listings = filtered_listings[filtered_listings['basement_size'].fillna(0) >= min_basement_size]

if show_city_in_zip:
    filtered_listings = filtered_listings[filtered_listings['is_in_zip_code_city'] == show_city_in_zip]

# Sort by dynamic score (highest first)
filtered_listings = filtered_listings.sort_values(by='dynamic_score', ascending=False)

# Display results
st.write(f"**Fandt {len(filtered_listings)} boliger der matcher dine kriterier**")

# Create tabs for different views
data_tab, scores_tab, seen_tab = st.tabs(["🏠 Boliger", "📊 Pointdetaljer", "🔍 Allerede sete huse"])
with data_tab:
    st.info("💡 **Vigtigt**: Pris-scoren baseres på **pris per m²**, ikke samlet pris. Dette betyder at et stort hus med lav m²-pris kan score højere end et lille hus med høj m²-pris.")
    
    # Main property information
    if not filtered_listings.empty:
            # Calculate and display summary statistics with enhanced styling
            st.markdown("### 📊 **Nøgletal**")
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                avg_price_rounded = round(filtered_listings['price'].mean() / 1000) * 1000
                st.metric(
                    label="💰 **Gennemsnitspris**", 
                    value=f"{avg_price_rounded:,.0f} kr",
                    delta=None,
                    help="Gennemsnitlig salgspris for filtrerede boliger, afrundet til nærmeste 1.000 kr"
                )

            with col2:
                median_price = filtered_listings['price'].median()
                st.metric(
                    label="📈 **Median pris**", 
                    value=f"{median_price:,.0f} kr",
                    help="Median salgspris - halvdelen af boligerne er dyrere, halvdelen billigere"
                )

            with col3:
                total_count = len(filtered_listings)
                st.metric(
                    label="🏠 **Antal boliger**", 
                    value=f"{total_count}",
                    help="Antal boliger der matcher dine filterkriterier"
                )
                
            with col4:
                avg_area = filtered_listings['m2'].mean()
                st.metric(
                    label="📐 **Gns. areal**", 
                    value=f"{avg_area:.0f} m²",
                    help="Gennemsnitligt boligareal i kvadratmeter"
                )
                
            with col5:
                avg_score = filtered_listings['dynamic_score'].mean()
                st.metric(
                    label="⭐ **Gns. Score**", 
                    value=f"{avg_score:.1f}/100",
                    help="Gennemsnitlig dynamisk score baseret på dine vægtningsindstillinger"
                )

            st.markdown("---")  # Visual separator

            # Add clickable Google search links for properties
            filtered_listings_display = filtered_listings.copy()
            
            def create_google_search_url(row):
                address = row['full_address']
                city = row['city']
                # Google search for property
                search_query = f'"{address}" "{city}"'
                # URL encode the search query
                import urllib.parse
                encoded_query = urllib.parse.quote(search_query)
                return f"https://www.google.com/search?q={encoded_query}"
            
            filtered_listings_display['search_link'] = filtered_listings_display.apply(
                create_google_search_url, axis=1
            )

            property_columns = ['full_address', 'city', 'price', 'm2_price', 'm2', 'rooms', 'built', 
                              'energy_class', 'lot_size', 'basement_size', 'days_on_market', 'dynamic_score', 'search_link']
            
            st.dataframe(
                data=filtered_listings_display[property_columns], 
                height=600, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "dynamic_score": st.column_config.NumberColumn("Samlet score", format="%.1f"),
                    "price": st.column_config.NumberColumn("Samlet pris", format="%d"),
                    "m2_price": st.column_config.NumberColumn("Pris/m² (scored)", format="%d"),
                    "m2": st.column_config.NumberColumn("m²", format="%d"),
                    "rooms": st.column_config.NumberColumn("Værelser", format="%d"),
                    "built": st.column_config.TextColumn("Byggeår"),
                    "energy_class": st.column_config.TextColumn("Energiklasse"),
                    "lot_size": st.column_config.NumberColumn("Grundstørrelse", format="%d"),
                    "basement_size": st.column_config.NumberColumn("Kælder", format="%d"),
                    "days_on_market": st.column_config.NumberColumn("Dage på marked", format="%d"),
                    "full_address": st.column_config.TextColumn("Adresse", width="large"),
                    "city": st.column_config.TextColumn("By", width="medium"),
                    "search_link": st.column_config.LinkColumn(
                        "Søg",
                        help="Søg efter denne bolig på Google",
                        width="small",
                        display_text="🔍"
                    )
                }
            )

            # Add to seen houses functionality
            st.subheader("Markér huse som sete")
            ouid_input = st.text_input("Indtast ouID'er adskilt af kommaer")
            if st.button("Tilføj til sete huse"):
                ouids = [ouid.strip() for ouid in ouid_input.split(",") if ouid.strip()]
                if ouids:
                    try:
                        for ouid in ouids:
                            add_seen_house(int(ouid))
                        st.success("ouID'er tilføjet til sete huse")
                        # Clear cache to refresh data
                        st.cache_data.clear()
                        st.rerun()
                    except ValueError:
                        st.error("Indtast venligst gyldige numeriske ouID'er")
                    except Exception as e:
                        st.error(f"Fejl ved tilføjelse: {e}")
                else:
                    st.error("Indtast venligst gyldige ouID'er")
    else:
        st.warning("Ingen boliger matcher dine filterkriterier.")

with scores_tab:
    if not filtered_listings.empty:
        # Show current weighting profile
        st.info(f"📊 **Aktuel vægtningsprofil:** {st.session_state.selected_profile}")
        
        # Display current weights
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Aktuelle vægte:**")
            for param, display_name in scoring_engine.SCORE_PARAMETERS.items():
                weight = st.session_state.current_weights[param]
                st.write(f"• {display_name}: {weight:.1f}%")
        
        with col2:
            # Show top scorer
            if len(filtered_listings) > 0:
                top_house = filtered_listings.iloc[0]
                st.write("**🏆 Bedste bolig:**")
                st.write(f"• {top_house['full_address']}")
                st.write(f"• Score: {top_house['dynamic_score']:.1f}/100")
                st.write(f"• Pris: {top_house['price']:,.0f} kr")
        
        # Score breakdown details with clickable links
        filtered_listings_scores = filtered_listings.copy()
        
        def create_google_search_url(row):
            address = row['full_address']
            city = row['city']
            # Google search for property
            search_query = f'"{address}" "{city}"'
            # URL encode the search query
            import urllib.parse
            encoded_query = urllib.parse.quote(search_query)
            return f"https://www.google.com/search?q={encoded_query}"
        
        filtered_listings_scores['search_link'] = filtered_listings_scores.apply(
            create_google_search_url, axis=1
        )
        
        score_columns = ['full_address', 'city', 'score_price_efficiency', 'score_house_size', 
                       'score_build_year', 'score_energy', 'score_lot_size', 
                       'score_basement', 'score_days_market', 'score_train_distance', 'dynamic_score', 'search_link']
        
        st.dataframe(
            data=filtered_listings_scores[score_columns], 
            height=500, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "score_price_efficiency": st.column_config.NumberColumn("Pris/m²", format="%.1f"),
                "score_house_size": st.column_config.NumberColumn("Størrelse", format="%.1f"),
                "score_build_year": st.column_config.NumberColumn("År", format="%.1f"),
                "score_energy": st.column_config.NumberColumn("Energi", format="%.1f"),
                "score_lot_size": st.column_config.NumberColumn("Grund", format="%.1f"),
                "score_basement": st.column_config.NumberColumn("Kælder", format="%.1f"),
                "score_days_market": st.column_config.NumberColumn("Marked", format="%.1f"),
                "score_train_distance": st.column_config.NumberColumn("Tog", format="%.1f"),
                "dynamic_score": st.column_config.NumberColumn("💯 Total", format="%.1f"),
                "full_address": st.column_config.TextColumn("Adresse", width="medium"),
                "city": st.column_config.TextColumn("By", width="small"),
                "search_link": st.column_config.LinkColumn(
                    "Søg",
                    help="Søg efter denne bolig på Google",
                    width="small",
                    display_text="🔍"
                )
            }
        )
    else:
        st.warning("Ingen boliger matcher dine filterkriterier.")

with seen_tab:
    # Seen Houses section
    st.subheader("🔍 Sete Huse")
    
    if not seen_houses.empty:
        # Join seen houses with listings for addresses
        seen_with_addresses = seen_houses.merge(
            listings_scored[['ouId', 'full_address']], 
            on='ouId', 
            how='left'
        )
        st.dataframe(
            data=seen_with_addresses[['full_address', 'seen_at']], 
            height=400, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "full_address": st.column_config.TextColumn("Adresse"),
                "seen_at": st.column_config.DatetimeColumn("Set dato")
            }
        )
    else:
        st.info("Ingen huse er markeret som sete endnu.")

# Add refresh data button
if st.sidebar.button("🔄 Genindlæs data"):
    st.cache_data.clear()
    st.rerun()

# Show data freshness
try:
    db = HousingDataDB()
    last_update = db.conn.execute("SELECT MAX(loaded_at_utc) as last_update FROM listings").fetchone()[0]
    if last_update:
        st.sidebar.info(f"Data sidst opdateret: {last_update}")
    db.close()
except Exception:
    pass
