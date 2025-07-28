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
from top_scorers import topscorer_calculator

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
st.title("🏠 Boligoversigt")

# Initialize session state for weights early
if 'current_weights' not in st.session_state:
    st.session_state.current_weights = scoring_engine.DEFAULT_WEIGHTS.copy()
if 'selected_profile' not in st.session_state:
    st.session_state.selected_profile = 'Standard (lige vægt)'
if 'weights_changed' not in st.session_state:
    st.session_state.weights_changed = False

# ======== VÆGTNINGS SEKTION (Ekspanderbar på hovedsiden) ========
with st.expander("⚖️ **Vægtning af parametre**", expanded=False):
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

        # Check if profile changed - don't collapse expander
        if selected_profile != st.session_state.selected_profile:
            st.session_state.selected_profile = selected_profile
            st.session_state.current_weights = scoring_engine.get_profile_weights(selected_profile)
            st.session_state.weights_changed = True
            # Don't rerun to keep expander open

        st.write(f"**Aktiv profil:** {selected_profile}")
    
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
            topscorer_calculator.clear_cache()  # Clear topscorer cache too
            st.rerun()

# ======== FILTER SEKTION ========
st.sidebar.title("🔍 **Filtrer Boliger**")

# Postnummer filter først
zip_codes = sorted(listings_scored['zip_code'].unique())
selected_zip_codes = st.sidebar.multiselect("Vælg postnumre", zip_codes, default=['8370','8382'])

# Enhanced filters
st.sidebar.subheader("📊 Basis Filtre")
max_budget = st.sidebar.number_input("Maksimalt budget", min_value=0, max_value=15000000, value=5000000, step=500000)
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

# Checkbox filtre i bunden
st.sidebar.subheader("🔧 Avancerede Filtre")
show_city_in_zip = st.sidebar.checkbox("Vis kun boliger med hvor bynavn er det samme som postnummeret", value=True)
show_already_seen_houses = st.sidebar.checkbox("Vis huse der allerede er markeret som set", value=False)

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

# ======== TOPSCORER SEKTION ========
st.markdown("### 🏆 **Topscorere**")

# Calculate topscorers based on filtered data
if not filtered_listings.empty:
    topscorers = topscorer_calculator.calculate_topscorers(filtered_listings)
    
    if topscorers:
        # Create expandable topscorer section
        with st.expander("🏆 **Se Topscorere**", expanded=True):
            # Display topscorers in a 4-column grid
            categories = list(topscorers.keys())
            
            # Create rows of 4 cards each
            for i in range(0, len(categories), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    if i + j < len(categories):
                        category_id = categories[i + j]
                        topscorer_data = topscorers[category_id]
                        
                        with col:
                            # Create card for each topscorer
                            card_html = f"""
                            <div style="
                                border: 2px solid #e1e5e9;
                                border-radius: 10px;
                                padding: 15px;
                                margin: 5px 0;
                                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                height: 200px;
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                            ">
                                <div style="text-align: center;">
                                    <div style="font-size: 2rem; margin-bottom: 5px;">
                                        {topscorer_data['icon']}
                                    </div>
                                    <div style="font-weight: bold; font-size: 0.9rem; color: #495057; margin-bottom: 8px;">
                                        {topscorer_data['name']}
                                    </div>
                                    <div style="font-size: 1.2rem; font-weight: bold; color: #28a745; margin-bottom: 8px;">
                                        {topscorer_data['winning_value']}
                                    </div>
                                </div>
                                <div style="border-top: 1px solid #dee2e6; padding-top: 10px;">
                                    <div style="font-size: 0.8rem; color: #6c757d; text-align: center; margin-bottom: 5px;">
                                        {topscorer_data['property']['full_address'][:30]}{'...' if len(topscorer_data['property']['full_address']) > 30 else ''}
                                    </div>
                                    <div style="font-size: 0.75rem; color: #868e96; text-align: center;">
                                        {topscorer_data['property']['city']} • {topscorer_data['property']['price']:,.0f} kr
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            # Add button to add to seen houses
                            if st.button(f"👁️ Markér som set", key=f"seen_{category_id}", help="Tilføj til sete huse"):
                                try:
                                    add_seen_house(int(topscorer_data['property']['ouId']))
                                    st.success(f"Bolig tilføjet til sete huse!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fejl: {e}")
    else:
        st.info("Ingen topscorere fundet for de aktuelle filtre.")
else:
    st.info("Ingen data tilgængelig for topscorere.")

st.markdown("---")  # Visual separator

# Display results
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

            # Tabel titel
            st.subheader("🏠 Alle Boliger")
            
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
                    "m2_price": st.column_config.NumberColumn(
                        "Pris/m²", 
                        format="%d",
                        help="💡 Pris-scoren baseres på pris per m², ikke samlet pris. Dette betyder at et stort hus med lav m²-pris kan score højere end et lille hus med høj m²-pris."
                    ),
                    "m2": st.column_config.NumberColumn("m²", format="%d"),
                    "rooms": st.column_config.NumberColumn("Værelser", format="%d"),
                    "built": st.column_config.TextColumn("Byggeår"),
                    "energy_class": st.column_config.TextColumn("Energiklasse"),
                    "lot_size": st.column_config.NumberColumn("Grundstørrelse", format="%d"),
                    "basement_size": st.column_config.NumberColumn("Kælderstørrelse", format="%d"),
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
else:
    st.warning("Ingen boliger matcher dine filterkriterier.")

# Add refresh data button
if st.sidebar.button("🔄 Genindlæs data"):
    st.cache_data.clear()
    scoring_engine.clear_cache()
    topscorer_calculator.clear_cache()
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
