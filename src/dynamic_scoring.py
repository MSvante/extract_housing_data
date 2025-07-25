"""
Dynamic Scoring Engine for Housing Data
Handles real-time score calculation with configurable weights
"""

import pandas as pd
import streamlit as st
from typing import Dict, Tuple
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DynamicScoringEngine:
    """
    Engine for calculating weighted scores based on user preferences.
    Handles caching and performance optimization for score calculations.
    """
    
    def __init__(self):
        """Initialize the scoring engine with default weights and profiles."""
        
        # Define all scoring parameters with their display names
        self.SCORE_PARAMETERS = {
            'score_energy': 'Energiklasse',
            'score_train_distance': 'Transport afstand',
            'score_lot_size': 'Grundstørrelse', 
            'score_house_size': 'Husstørrelse',
            'score_price_efficiency': 'Priseffektivitet',
            'score_build_year': 'Byggeår',
            'score_basement': 'Kælderstørrelse',
            'score_days_market': 'Dage på marked'
        }
        
        # Default weights (equal distribution)
        self.DEFAULT_WEIGHTS = {param: 12.5 for param in self.SCORE_PARAMETERS.keys()}
        
        # Predefined user profiles
        self.PROFILES = {
            'Standard (lige vægt)': {
                'score_energy': 12.5,
                'score_train_distance': 12.5,
                'score_lot_size': 12.5,
                'score_house_size': 12.5,
                'score_price_efficiency': 12.5,
                'score_build_year': 12.5,
                'score_basement': 12.5,
                'score_days_market': 12.5
            },
            'Familievenlig': {
                'score_house_size': 20.0,
                'score_lot_size': 20.0,
                'score_build_year': 15.0,
                'score_energy': 15.0,
                'score_basement': 10.0,
                'score_train_distance': 10.0,
                'score_price_efficiency': 5.0,
                'score_days_market': 5.0
            },
            'Investering': {
                'score_price_efficiency': 25.0,
                'score_days_market': 20.0,
                'score_train_distance': 15.0,
                'score_energy': 15.0,
                'score_house_size': 10.0,
                'score_build_year': 10.0,
                'score_lot_size': 3.0,
                'score_basement': 2.0
            },
            'Førstegangskøber': {
                'score_price_efficiency': 30.0,
                'score_energy': 20.0,
                'score_train_distance': 15.0,
                'score_house_size': 15.0,
                'score_build_year': 10.0,
                'score_days_market': 5.0,
                'score_lot_size': 3.0,
                'score_basement': 2.0
            },
            'Pensionist': {
                'score_energy': 25.0,
                'score_train_distance': 20.0,
                'score_build_year': 15.0,
                'score_house_size': 15.0,
                'score_price_efficiency': 10.0,
                'score_days_market': 10.0,
                'score_lot_size': 3.0,
                'score_basement': 2.0
            },
            'Miljøbevidst': {
                'score_energy': 35.0,
                'score_train_distance': 25.0,
                'score_build_year': 15.0,
                'score_price_efficiency': 10.0,
                'score_house_size': 8.0,
                'score_days_market': 4.0,
                'score_lot_size': 2.0,
                'score_basement': 1.0
            }
        }
        
        # Cache for score calculations
        self._score_cache = {}
        
    def validate_weights(self, weights: Dict[str, float]) -> Tuple[bool, str]:
        """
        Validate that weights sum to 100% and all parameters are present.
        
        Args:
            weights: Dictionary of parameter -> weight mappings
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check all parameters are present
        missing_params = set(self.SCORE_PARAMETERS.keys()) - set(weights.keys())
        if missing_params:
            return False, f"Missing parameters: {missing_params}"
        
        # Check weights sum to 100 (with small tolerance for floating point)
        total_weight = sum(weights.values())
        if abs(total_weight - 100.0) > 0.01:
            return False, f"Weights sum to {total_weight:.1f}%, must equal 100%"
        
        # Check all weights are non-negative
        negative_weights = [k for k, v in weights.items() if v < 0]
        if negative_weights:
            return False, f"Negative weights not allowed: {negative_weights}"
        
        return True, ""
    
    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize weights to sum to exactly 100%.
        
        Args:
            weights: Dictionary of parameter -> weight mappings
            
        Returns:
            Normalized weights dictionary
        """
        total = sum(weights.values())
        if total == 0:
            return self.DEFAULT_WEIGHTS.copy()
        
        return {k: (v / total) * 100.0 for k, v in weights.items()}
    
    def calculate_weighted_scores(self, df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        """
        Calculate total scores using provided weights.
        
        Args:
            df: DataFrame with individual score columns
            weights: Dictionary of parameter -> weight mappings
            
        Returns:
            DataFrame with added 'total_score' column
        """
        # Validate weights
        is_valid, error_msg = self.validate_weights(weights)
        if not is_valid:
            st.error(f"Weight validation failed: {error_msg}")
            weights = self.DEFAULT_WEIGHTS
        
        # Generate cache key based on weights and data shape
        weight_signature = self._generate_weight_signature(weights, df)
        
        # Check cache first
        if weight_signature in self._score_cache:
            logging.info("Using cached score calculation")
            return self._score_cache[weight_signature].copy()
        
        # Calculate weighted scores
        df_result = df.copy()
        
        # Ensure all score columns exist, fill missing with 0
        for param in self.SCORE_PARAMETERS.keys():
            if param not in df_result.columns:
                df_result[param] = 0.0
                logging.warning(f"Missing score column {param}, filled with 0")
        
        # Calculate total score
        total_score = pd.Series(0.0, index=df_result.index)
        for param, weight in weights.items():
            if param in df_result.columns:
                total_score += df_result[param] * (weight / 100.0)
        
        df_result['total_score'] = total_score.round(2)
        
        # Cache result (limit cache size)
        if len(self._score_cache) > 10:  # Simple cache eviction
            oldest_key = next(iter(self._score_cache))
            del self._score_cache[oldest_key]
        
        self._score_cache[weight_signature] = df_result.copy()
        logging.info(f"Calculated and cached scores for {len(df_result)} listings")
        
        return df_result
    
    def _generate_weight_signature(self, weights: Dict[str, float], df: pd.DataFrame) -> str:
        """Generate a hash signature for caching based on weights and data."""
        # Create signature from weights and data shape
        weight_str = ','.join(f"{k}:{v:.3f}" for k, v in sorted(weights.items()))
        data_signature = f"rows:{len(df)},cols:{len(df.columns)}"
        
        combined = f"{weight_str}|{data_signature}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def get_profile_weights(self, profile_name: str) -> Dict[str, float]:
        """
        Get weights for a specific profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary of weights for the profile
        """
        return self.PROFILES.get(profile_name, self.DEFAULT_WEIGHTS).copy()
    
    def get_profile_names(self) -> list:
        """Get list of available profile names."""
        return list(self.PROFILES.keys())
    
    def clear_cache(self):
        """Clear the score calculation cache."""
        self._score_cache.clear()
        logging.info("Score cache cleared")
    
    def get_parameter_display_name(self, param: str) -> str:
        """Get the display name for a parameter."""
        return self.SCORE_PARAMETERS.get(param, param)
    
    def apply_scoring(self, df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        """
        Apply dynamic scoring to a DataFrame with configurable weights.
        
        Args:
            df: DataFrame with individual score components
            weights: Dictionary of weights for each parameter (should sum to 100)
            
        Returns:
            DataFrame with added 'dynamic_score' column
        """
        # Generate cache signature
        cache_key = self._generate_weight_signature(weights, df)
        
        # Check cache first
        if cache_key in self._score_cache:
            logging.info(f"Using cached scores for signature: {cache_key}")
            df_result = df.copy()
            df_result['dynamic_score'] = self._score_cache[cache_key]
            return df_result
        
        # Validate weights
        total_weight = sum(weights.values())
        if abs(total_weight - 100.0) > 0.1:
            st.warning(f"⚠️ Vægtene summer til {total_weight:.1f}% i stedet for 100%")
            # Normalize weights to 100%
            weights = self.normalize_weights(weights)
        
        # Calculate dynamic scores
        df_result = df.copy()
        dynamic_scores = []
        
        for _, row in df.iterrows():
            total_score = 0.0
            
            for param, weight in weights.items():
                if param in row and pd.notna(row[param]):
                    # Each individual score is 0-10, weight is percentage
                    total_score += (row[param] * weight / 100.0)
            
            # Scale to 0-100 range (since each component is 0-10 and weights sum to 100%)
            scaled_score = total_score * 10  # 10 components * 10 max points = 100 max
            dynamic_scores.append(round(scaled_score, 1))
        
        # Cache the results
        self._score_cache[cache_key] = dynamic_scores
        df_result['dynamic_score'] = dynamic_scores
        
        logging.info(f"Calculated {len(dynamic_scores)} dynamic scores with signature {cache_key}")
        return df_result

# Global instance for use in Streamlit app
scoring_engine = DynamicScoringEngine()
