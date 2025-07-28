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

    # Weight sliders in full width
    st.write("**Juster vægtning (%):**")
    temp_weights = {}
    total_weight = 0

    # Create two columns for sliders
    slider_col1, slider_col2 = st.columns(2)
    params_list = list(scoring_engine.SCORE_PARAMETERS.items())
    mid_point = len(params_list) // 2
        
    with slider_col1:
        for param, label in params_list[:mid_point]:
            temp_weights[param] = st.slider(
                label,
                min_value=0,
                max_value=50,
                value=int(st.session_state.current_weights[param]),
                key=f"weight_{param}",
                help=f"Vægtning for {label.lower()}"
            )
            total_weight += temp_weights[param]

    with slider_col2:
        for param, label in params_list[mid_point:]:
            temp_weights[param] = st.slider(
                label,
                min_value=0,
                max_value=50,
                value=int(st.session_state.current_weights[param]),
                key=f"weight_{param}",
                help=f"Vægtning for {label.lower()}"
            )
            total_weight += temp_weights[param]

    # Show total weight only if it's not 100%
    if total_weight != 100:
        if total_weight > 100:
            st.error(f"⚠️ **Total vægtning: {total_weight}%** (Reducér nogle vægte)")
        else:
            st.warning(f"⚠️ **Total vægtning: {total_weight}%** (Mangler {100-total_weight}%)")
    
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
    total_count = len(filtered_listings)
    avg_area = filtered_listings['m2'].mean()
    avg_score = filtered_listings['dynamic_score'].mean()
    
    # Create HTML cards for key metrics (similar to topscorer cards)
    metrics_data = [
        {
            'icon': '💰',
            'name': 'Gennemsnitspris',
            'value': f"{avg_price_rounded:,.0f} kr",
            'description': 'Gns. salgspris afrundet til nærmeste 1.000 kr'
        },
        {
            'icon': '📈',
            'name': 'Median pris',
            'value': f"{median_price:,.0f} kr",
            'description': 'Halvdelen af boligerne er dyrere/billigere'
        },
        {
            'icon': '🏠',
            'name': 'Antal boliger',
            'value': f"{total_count}",
            'description': 'Boliger der matcher dine filterkriterier'
        },
        {
            'icon': '📐',
            'name': 'Gns. areal',
            'value': f"{avg_area:.0f} m²",
            'description': 'Gennemsnitligt boligareal'
        },
        {
            'icon': '⭐',
            'name': 'Gns. Score',
            'value': f"{avg_score:.1f}/100",
            'description': 'Baseret på dine vægtningsindstillinger'
        }
    ]
    
    # Display metrics in rows of 5
    cols = st.columns(5)
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            card_html = f"""
            <div style="
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                padding: 15px;
                margin: 5px 0;
                background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                height: 140px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                text-align: center;
            ">
                <div style="font-size: 2rem; margin-bottom: 10px;">
                    {metric['icon']}
                </div>
                <div style="font-weight: bold; font-size: 0.9rem; color: #495057; margin-bottom: 8px;">
                    {metric['name']}
                </div>
                <div style="font-size: 1.3rem; font-weight: bold; color: #2c5aa0;">
                    {metric['value']}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

# ======== TOPSCORER SEKTION ========
st.markdown("### 🏆 **Topscorere**")

# Calculate topscorers based on filtered data
if not filtered_listings.empty:
    topscorers = topscorer_calculator.calculate_topscorers(filtered_listings)
    
    # If topscorer_calculator failed, use manual topscorer as fallback
    if not topscorers:
        top_row = filtered_listings.sort_values(by='dynamic_score', ascending=False).iloc[0]
        topscorers = {
            'best_overall': {
                'name': 'Bedste Samlet Score',
                'icon': '🏆',
                'property': dict(top_row),
                'winning_value': f"{top_row['dynamic_score']:.1f}/100"
            }
        }
    
    if topscorers:
        # Display topscorers directly without expander
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
        st.write("**Hurtig markering:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Select properties to mark as seen
            if st.button("📋 Marker valgte som set", help="Vælg rækker i tabellen ovenfor og klik her", key="main_mark_selected"):
                if hasattr(st.session_state, 'selected_properties') and st.session_state.selected_properties:
                    try:
                        db = HousingDataDB()
                        db.add_seen_listings_batch(st.session_state.selected_properties)
                        db.close()
                        st.success(f"Markerede {len(st.session_state.selected_properties)} huse som sete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fejl: {e}")
                else:
                    st.warning("Ingen huse valgt")
        
        with col2:
            # Mark all visible as seen
            if st.button("✅ Marker alle synlige som set", help="Marker alle viste huse som sete", key="main_mark_all"):
                try:
                    visible_ids = filtered_listings_display['ouId'].tolist()
                    db = HousingDataDB()
                    db.add_seen_listings_batch(visible_ids)
                    db.close()
                    st.success(f"Markerede {len(visible_ids)} huse som sete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fejl: {e}")
        
        with col3:
            # Individual property marking (simple input)
            property_id = st.number_input("Marker enkelt hus (ouId)", min_value=1, step=1, key="main_mark_single")
            if st.button("�️ Marker som set", key="main_mark_single_btn"):
                try:
                    db = HousingDataDB()
                    db.add_seen_listing(int(property_id))
                    db.close()
                    st.success(f"Hus {property_id} markeret som set!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fejl: {e}")
    
    with tab2:
        # Move seen listings management section to separate tab
        st.subheader("👁️ Administrer Sete Huse")
        
        # Show statistics
        try:
            db = HousingDataDB()
            stats = db.get_seen_listings_stats()
            db.close()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total sete", stats['total_seen'])
            with col2:
                st.metric("Sete denne uge", stats['seen_last_7_days'])
            with col3:
                st.metric("Med bedømmelse", stats['rated_count'])
            with col4:
                st.metric("Gns. bedømmelse", f"{stats['avg_rating']}/5" if stats['avg_rating'] > 0 else "Ingen")
        except Exception as e:
            st.error(f"Kunne ikke hente statistikker: {e}")
        
        # Batch operations
        st.write("**Hurtig markering:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Clear all seen listings
            if st.button("🗑️ Fjern alle sete huse", help="Fjern alle huse fra 'set' listen", key="admin_clear_all"):
                try:
                    db = HousingDataDB()
                    db.clear_seen_listings()
                    db.close()
                    st.success("Alle sete huse er fjernet!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fejl: {e}")
        
        with col2:
            # Individual property marking (simple input)
            property_id = st.number_input("Marker enkelt hus (ouId)", min_value=1, step=1, key="admin_mark_single")
            if st.button("👁️ Marker som set", key="admin_mark_single_btn"):
                try:
                    db = HousingDataDB()
                    db.add_seen_listing(int(property_id))
                    db.close()
                    st.success(f"Hus {property_id} markeret som set!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fejl: {e}")
        
        with col3:
            # Export functionality placeholder
            st.info("📄 Export funktionalitet kommer senere")
        
        # Show seen listings table
        try:
            db = HousingDataDB()
            seen_listings = db.get_seen_listings()
            db.close()
            
            if not seen_listings.empty:
                st.write("**📋 Alle Sete Huse:**")
                
                # Merge with property details for display if possible
                try:
                    # Join with listings to get property details
                    seen_with_details = seen_listings.merge(
                        filtered_listings_display[['ouId', 'full_address', 'city', 'price', 'm2_price', 'm2', 'dynamic_score']],
                        on='ouId', 
                        how='left'
                    )
                    
                    seen_display_cols = ['ouId', 'full_address', 'city', 'price', 'm2_price', 'm2', 'dynamic_score', 
                                       'marked_seen_at', 'notes', 'user_rating']
                    
                    st.dataframe(
                        seen_with_details[seen_display_cols],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "ouId": st.column_config.NumberColumn("Bolig ID", format="%d"),
                            "full_address": st.column_config.TextColumn("Adresse", width="large"),
                            "city": st.column_config.TextColumn("By"),
                            "price": st.column_config.NumberColumn("Pris", format="%.0f"),
                            "m2_price": st.column_config.NumberColumn("Pris/m²", format="%.0f"),
                            "m2": st.column_config.NumberColumn("m²", format="%.0f"),
                            "dynamic_score": st.column_config.NumberColumn("Score", format="%.1f"),
                            "marked_seen_at": st.column_config.DatetimeColumn("Markeret som set"),
                            "notes": st.column_config.TextColumn("Noter"),
                            "user_rating": st.column_config.NumberColumn("Bedømmelse", format="%.0f")
                        }
                    )
                    
                except Exception as e:
                    st.error(f"Kunne ikke indlæse boligdetaljer: {e}")
                    st.dataframe(seen_listings, use_container_width=True)
            
            else:
                st.info("Ingen huse er markeret som sete endnu.")
                st.write("Brug funktionerne ovenfor for at markere huse som sete.")
        
        except Exception as e:
            st.error(f"Fejl ved indlæsning af sete huse: {e}")
            
else:
    st.warning("Ingen boliger matcher dine filterkriterier.")

# Add refresh data button and clear seen houses
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Genindlæs data"):
        st.cache_data.clear()
        scoring_engine.clear_cache()
        topscorer_calculator.clear_cache()
        st.rerun()

with col2:
    if st.button("👁️ Nulstil sete huse", help="Fjern alle huse fra 'set' listen"):
        try:
            db = HousingDataDB()
            db.clear_seen_listings()
            db.close()
            st.success("Alle sete huse er fjernet!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Fejl ved sletning: {e}")

# Show data freshness
try:
    db = HousingDataDB()
    last_update = db.conn.execute("SELECT MAX(loaded_at_utc) as last_update FROM listings").fetchone()[0]
    if last_update:
        st.sidebar.info(f"Data sidst opdateret: {last_update}")
    db.close()
except Exception:
    pass
