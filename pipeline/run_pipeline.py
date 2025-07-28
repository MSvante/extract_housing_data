#!/home/mser/code/repos/housing_data_extract/venv/bin/python
"""
Main Housing Data Pipeline
Local version - extracts, transforms, and stores housing data
"""

import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from extract_listings_local import extract_all_listings
from transform_listings_local import transform_listings
from database_local import HousingDataDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/housing_pipeline.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Run the full data pipeline."""
    logging.info("Starting housing data pipeline...")
    
    try:
        # Initialize database
        logging.info("Initializing database...")
        db = HousingDataDB()
        
        # Extract data
        logging.info("Extracting listings data...")
        df_raw = extract_all_listings()
        
        if df_raw.empty:
            logging.error("No data extracted. Exiting.")
            return False
        
        # Clear old data and insert new raw data
        db.truncate_listings()
        db.insert_listings(df_raw)
        
        # Transform data
        logging.info("Transforming and scoring listings...")
        df_scored = transform_listings(df_raw)
        
        # Apply dynamic scoring to get dynamic_score for pipeline stats
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent / 'src'))
        from dynamic_scoring import scoring_engine
        df_with_dynamic_score = scoring_engine.apply_scoring(df_scored, scoring_engine.DEFAULT_WEIGHTS)
        
        # Insert scored data (without dynamic_score column as it's calculated in frontend)
        db.insert_scored_listings(df_scored)
        
        logging.info(f"Pipeline completed successfully. Processed {len(df_scored)} listings.")
        
        # Show some stats using the data with dynamic scores
        try:
            top_scores = df_with_dynamic_score.nlargest(5, 'dynamic_score')[['dynamic_score', 'price']]
            logging.info(f"Top 5 scored properties:\n{top_scores}")
        except Exception as e:
            logging.warning(f"Could not display top scores: {e}")
            logging.info(f"Pipeline completed with {len(df_scored)} properties processed")
        
        db.close()
        return True
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
