"""
Local Housing Data Streamlit App
Migrated from Databricks to work with local DuckDB
"""

import sys
from pathlib import Path
import streamlit as st
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from database_local import HousingDataDB
from dynamic_scoring import scoring_engine
from top_scorers import topscorer_calculator

st.set_page_config(layout="wide", page_title="🏠 Boligoversigt")

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_listings_data():
    """Get listings data from local database."""
    db = HousingDataDB()
    try:
        listings_scored = db.get_listings_for_streamlit()
        return listings_scored
    finally:
        db.close()

# Load data
try:
    listings_scored = get_listings_data()
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
    # Profile selector at the top
    profile_names = scoring_engine.get_profile_names()
    # Add 'Custom' to profile names if not already there
    if 'Custom' not in profile_names:
        profile_names.append('Custom')
    
    # Ensure selected profile exists in list
    if st.session_state.selected_profile not in profile_names:
        st.session_state.selected_profile = profile_names[0]
        
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

    # Create sliders for weights
    col1, col2 = st.columns(2)
    
    with col1:
        energy_weight = st.slider("🔋 Energiklasse", 0.0, 100.0, st.session_state.current_weights['score_energy'], step=0.1, format="%.1f", key="energy_slider")
        train_weight = st.slider("🚆 Transport", 0.0, 100.0, st.session_state.current_weights['score_train_distance'], step=0.1, format="%.1f", key="train_slider")
        lot_weight = st.slider("🌳 Grundstørrelse", 0.0, 100.0, st.session_state.current_weights['score_lot_size'], step=0.1, format="%.1f", key="lot_slider")
        house_weight = st.slider("🏠 Husstørrelse", 0.0, 100.0, st.session_state.current_weights['score_house_size'], step=0.1, format="%.1f", key="house_slider")
    
    with col2:
        price_weight = st.slider("💰 Priseffektivitet", 0.0, 100.0, st.session_state.current_weights['score_price_efficiency'], step=0.1, format="%.1f", key="price_slider")
        build_weight = st.slider("🏗️ Byggeår", 0.0, 100.0, st.session_state.current_weights['score_build_year'], step=0.1, format="%.1f", key="build_slider")
        basement_weight = st.slider("🏠 Kælderstørrelse", 0.0, 100.0, st.session_state.current_weights['score_basement'], step=0.1, format="%.1f", key="basement_slider")
        market_weight = st.slider("⏰ Dage på marked", 0.0, 100.0, st.session_state.current_weights['score_days_market'], step=0.1, format="%.1f", key="market_slider")

    # Calculate total and check if changed
    current_total = energy_weight + train_weight + lot_weight + house_weight + price_weight + build_weight + basement_weight + market_weight
    
    # Show total with color coding
    if current_total == 100:
        st.success(f"✅ Total vægtning: {current_total}%")
    else:
        st.error(f"⚠️ Total vægtning: {current_total}% (skal være 100%)")
    
    # Check if weights have changed
    new_weights = {
        'score_energy': energy_weight,
        'score_train_distance': train_weight,
        'score_lot_size': lot_weight,
        'score_house_size': house_weight,
        'score_price_efficiency': price_weight,
        'score_build_year': build_weight,
        'score_basement': basement_weight,
        'score_days_market': market_weight
    }
    
    weights_changed = new_weights != st.session_state.current_weights
    if weights_changed:
        st.session_state.current_weights = new_weights
        st.session_state.weights_changed = True
        if selected_profile != 'Custom':
            st.session_state.selected_profile = 'Custom'
    
    # Recalculate button
    recalc_disabled = not st.session_state.weights_changed or current_total != 100
    if st.button("🔄 Genberegn Scores", disabled=recalc_disabled, type="primary", key="main_recalc_scores"):
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
min_build_year = st.sidebar.number_input("Minimum byggeår", min_value=1800, max_value=2025)
energy_classes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'UNKNOWN']
selected_energy_classes = st.sidebar.multiselect("Energiklasser", energy_classes, default=[])

min_lot_size = st.sidebar.number_input("Minimum grundstørrelse (m²)", min_value=0, max_value=5000, value=0)
min_basement_size = st.sidebar.number_input("Minimum kælderstørrelse (m²)", min_value=0, max_value=500, value=0)

# Checkbox filtre i bunden
st.sidebar.subheader("🔧 Avancerede Filtre")
show_city_in_zip = st.sidebar.checkbox("Vis kun boliger med hvor bynavn er det samme som postnummeret", value=True)

# Apply dynamic scoring to filtered listings
filtered_listings = scoring_engine.apply_scoring(listings_scored, st.session_state.current_weights)

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

# ======== NØGLETAL SEKTION ========
if not filtered_listings.empty:
    st.markdown("### 📊 **Nøgletal**")
    
    # Calculate key metrics
    avg_price_rounded = round(filtered_listings['price'].mean() / 1000) * 1000
    median_price = filtered_listings['price'].median()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Antal boliger", len(filtered_listings))
    with col2:
        st.metric("Gennemsnitspris", f"{avg_price_rounded:,.0f} kr")
    with col3:
        st.metric("Median pris", f"{median_price:,.0f} kr")
    with col4:
        avg_score = filtered_listings['dynamic_score'].mean()
        st.metric("Gennemsnit score", f"{avg_score:.1f}")

# ======== TOPSCORER SEKTION ========
if not filtered_listings.empty:
    st.markdown("### 🏆 **Topscorere**")
    
    # Calculate topscorers using the calculator
    topscorers = topscorer_calculator.calculate_topscorers(filtered_listings)
    
    if topscorers:
        # Display in a grid of 4 columns
        cols = st.columns(4)
        
        for i, (category, topscorer_data) in enumerate(topscorers.items()):
            with cols[i % 4]:
                # Create a styled card
                card_html = f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: #f9f9f9; height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="font-weight: bold; font-size: 0.9rem; color: #495057; margin-bottom: 8px;">
                            {topscorer_data['name']}
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: #28a745; margin-bottom: 8px;">
                            {topscorer_data['winning_value']}
                        </div>
                    </div>
                    <div style="border-top: 1px solid #dee2e6; padding-top: 10px;">
                        <div style="font-size: 0.8rem; color: #6c757d; text-align: center; margin-bottom: 5px;">
                            {topscorer_data['property']['address_text']} {topscorer_data['property']['house_number']}
                        </div>
                        <div style="font-size: 0.75rem; color: #868e96; text-align: center;">
                            {topscorer_data['property']['city']} • {topscorer_data['property']['price']:,.0f} kr
                        </div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("Ingen topscorere fundet for de aktuelle filtre.")
else:
    st.info("Ingen data tilgængelig for topscorere.")

# Display results
# Main property information
if not filtered_listings.empty:
    # Add clickable Google search links for properties
    filtered_listings_display = filtered_listings.copy()
    
    # Create full_address column for display and search
    filtered_listings_display['full_address'] = (
        filtered_listings_display['address_text'].astype(str) + ' ' + 
        filtered_listings_display['house_number'].astype(str)
    )
    
    def create_google_search_url(row):
        address = row['full_address']
        city = row['city']
        # Google search for property
        search_query = f'{address} {city}'
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
