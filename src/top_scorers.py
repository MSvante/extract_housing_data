"""
Topscorer Calculator for Housing Data
Calculates and manages top-scoring properties across different categories
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TopScorerCalculator:
    """
    Calculates top scoring properties across different categories.
    Each category highlights the best property in that specific metric.
    """
    
    # Define scoring categories and their corresponding columns/logic
    CATEGORIES = {
        'best_overall': {
            'name': 'Bedste Samlet Score',
            'icon': '🏆',
            'column': 'dynamic_score',
            'ascending': False,
            'description': 'Højeste samlede score baseret på vægtning'
        },
        'cheapest_per_m2': {
            'name': 'Billigste per m²',
            'icon': '💰',
            'column': 'm2_price',
            'ascending': True,
            'description': 'Laveste pris per kvadratmeter'
        },
        'largest_house': {
            'name': 'Største Hus',
            'icon': '🏠',
            'column': 'm2',
            'ascending': False,
            'description': 'Største boligareal'
        },
        'newest_build': {
            'name': 'Nyeste Byggeår',
            'icon': '🆕',
            'column': 'built',
            'ascending': False,
            'description': 'Nyeste byggeår'
        },
        'best_energy': {
            'name': 'Bedste Energi',
            'icon': '⚡',
            'column': 'energy_class',
            'ascending': True,  # A is better than G
            'description': 'Bedste energiklasse'
        },
        'largest_lot': {
            'name': 'Størst Grund',
            'icon': '🌳',
            'column': 'lot_size',
            'ascending': False,
            'description': 'Største grundstørrelse'
        },
        'closest_transport': {
            'name': 'Tættest Transport',
            'icon': '🚂',
            'column': 'score_train_distance',
            'ascending': False,  # Higher score = closer to transport
            'description': 'Tættest på offentlig transport'
        },
        'fastest_sale': {
            'name': 'Hurtigst Salg',
            'icon': '⚡',
            'column': 'days_on_market',
            'ascending': True,
            'description': 'Færrest dage på marked'
        }
    }
    
    def __init__(self):
        """Initialize the TopScorerCalculator."""
        self.last_calculated_topscorers: Optional[Dict] = None
        self.last_data_hash: Optional[str] = None
    
    def calculate_topscorers(self, data: pd.DataFrame) -> Dict[str, Dict]:
        """
        Calculate top scoring properties for each category.
        
        Args:
            data: DataFrame with housing data
            
        Returns:
            Dictionary with category as key and property data as value
        """
        if data.empty:
            return {}
        
        # Create data hash for caching
        data_hash = str(hash(str(data.values.tobytes())))
        if data_hash == self.last_data_hash and self.last_calculated_topscorers:
            logger.info("Using cached topscorer calculations")
            return self.last_calculated_topscorers
        
        topscorers = {}
        
        for category_id, category_config in self.CATEGORIES.items():
            try:
                top_property = self._get_top_property(data, category_config)
                if top_property is not None:
                    topscorers[category_id] = {
                        **category_config,
                        'property': top_property,
                        'winning_value': self._get_winning_value(top_property, category_config)
                    }
                else:
                    logger.warning(f"No top property found for category: {category_id}")
                    
            except Exception as e:
                logger.error(f"Error calculating topscorer for {category_id}: {e}")
                continue
        
        # Cache results
        self.last_calculated_topscorers = topscorers
        self.last_data_hash = data_hash
        
        return topscorers
    
    def _get_top_property(self, data: pd.DataFrame, category_config: Dict) -> Optional[Dict]:
        """
        Get the top property for a specific category.
        
        Args:
            data: DataFrame with housing data
            category_config: Configuration for the category
            
        Returns:
            Dictionary with property data or None if no valid property found
        """
        column = category_config['column']
        ascending = category_config['ascending']
        
        # Handle missing column
        if column not in data.columns:
            logger.warning(f"Column {column} not found in data")
            return None
        
        # Filter out invalid values
        valid_data = data.copy()
        
        # Special handling for energy class
        if column == 'energy_class':
            # Define energy class ranking (A is best, G is worst)
            energy_ranking = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}
            valid_data = valid_data[valid_data[column].isin(energy_ranking.keys())].copy()
            if valid_data.empty:
                return None
            valid_data['energy_rank'] = valid_data[column].map(energy_ranking)
            sort_column = 'energy_rank'
        else:
            # Remove null values and ensure numeric columns are valid
            valid_data = valid_data.dropna(subset=[column])
            if valid_data.empty:
                return None
            sort_column = column
        
        # Sort and get top property
        try:
            sorted_data = valid_data.sort_values(by=sort_column, ascending=ascending)
            top_row = sorted_data.iloc[0]
            
            # Convert to dictionary and ensure serializable types
            property_dict = {}
            for col, val in top_row.items():
                if pd.isna(val):
                    property_dict[col] = None
                elif isinstance(val, (pd.Timestamp, pd.NaT)):
                    property_dict[col] = str(val)
                else:
                    property_dict[col] = val
            
            return property_dict
            
        except Exception as e:
            logger.error(f"Error sorting data for column {column}: {e}")
            return None
    
    def _get_winning_value(self, property_data: Dict, category_config: Dict) -> str:
        """
        Get formatted winning value for display.
        
        Args:
            property_data: Property data dictionary
            category_config: Category configuration
            
        Returns:
            Formatted string of the winning value
        """
        column = category_config['column']
        value = property_data.get(column)
        
        if value is None:
            return "N/A"
        
        # Format based on column type
        if column == 'dynamic_score':
            return f"{value:.1f}/100"
        elif column in ['m2_price', 'price']:
            return f"{value:,.0f} kr"
        elif column in ['m2', 'lot_size', 'basement_size']:
            return f"{value:,.0f} m²"
        elif column == 'built':
            return str(int(value))
        elif column == 'days_on_market':
            return f"{value} dage"
        elif column == 'energy_class':
            return str(value)
        elif column == 'score_train_distance':
            return f"{value:.1f}/10"
        else:
            return str(value)
    
    def get_category_info(self, category_id: str) -> Optional[Dict]:
        """
        Get information about a specific category.
        
        Args:
            category_id: ID of the category
            
        Returns:
            Category configuration dictionary or None
        """
        return self.CATEGORIES.get(category_id)
    
    def clear_cache(self):
        """Clear cached calculations."""
        self.last_calculated_topscorers = None
        self.last_data_hash = None
        logger.info("TopScorer cache cleared")

# Global instance
topscorer_calculator = TopScorerCalculator()
