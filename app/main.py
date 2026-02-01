import pandas as pd
import numpy as np
import streamlit as st
import json
from pathlib import Path
from dotenv import load_dotenv

from utils.database import DatabaseManager
from utils.normalizer import DataNormalizer

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="CSV to JSON Normalizer",
    page_icon="📊",
    layout="wide"
)

# Display logo
logo_path = Path(__file__).parent / "assets" / "image.png"
if logo_path.exists():
    st.image(str(logo_path), width=200)

st.title("CSV to JSON Normalizer")
st.markdown("Upload a CSV file to normalize data and export to JSON format")

# Initialize database connection
@st.cache_resource
def init_database():
    """Initialize database connection and create tables"""
    db = DatabaseManager()
    if db.connect():
        db.create_tables()
        return db
    return None

db = init_database()

if db is None:
    st.error("⚠️ Unable to connect to database. Please check your database configuration.")
    st.info("Make sure PostgreSQL is running and the environment variables are set correctly.")
else:
    st.success("✅ Database connected successfully")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

if uploaded_file is not None:
    try:
        # Read CSV file
        df = pd.read_csv(uploaded_file)
        
        # Replace NaN with None for JSON compatibility
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notna(df), None)
        
        st.subheader("Original Data Preview")
        st.dataframe(df.head(10))
        
        # Process button
        if st.button("Process and Normalize Data", type="primary"):
            with st.spinner("Processing data..."):
                # Convert DataFrame to list of dicts for original data storage
                original_data = df.to_dict('records')
                
                # Process and normalize data
                entries, errors = DataNormalizer.process_csv_data(df)
                
                # Create result JSON
                result = {
                    "entries": entries,
                    "errors": errors
                }
                
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Successfully Processed", len(entries))
                with col2:
                    st.metric("Errors", len(errors))
                
                # Show normalized data
                if entries:
                    st.subheader("Normalized Entries")
                    st.json(entries)
                
                # Show errors
                if errors:
                    st.subheader("Error Lines")
                    st.warning(f"Lines with errors: {errors}")
                
                # Save to database
                if db:
                    try:
                        # Insert original data
                        original_id = db.insert_original_data(original_data)
                        st.write(f"DEBUG: Original ID = {original_id}, Entries count = {len(entries)}")
                        
                        if original_id and entries:
                            # Insert normalized data
                            success = db.insert_normalized_data(entries, original_id)
                            if success:
                                st.success("✅ Data saved to database successfully!")
                            else:
                                st.error("❌ Failed to save normalized data")
                        elif not original_id:
                            st.error("❌ Failed to save original data")
                        elif not entries:
                            st.warning("⚠️ No valid entries to save")
                    except Exception as e:
                        st.error(f"Error saving to database: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                
                # Save to JSON file
                output_dir = Path(__file__).parent.parent / "output"
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / "result.json"
                try:
                    with open(output_path, 'w') as f:
                        json.dump(result, f, indent=2, sort_keys=True)
                    
                    st.success(f"✅ JSON file created: output/result.json")
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download result.json",
                        data=json.dumps(result, indent=2, sort_keys=True),
                        file_name="result.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"Error creating JSON file: {e}")
        
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.info("Please make sure your CSV file is in one of the 3 supported formats. See sidebar for details.")

# Color Statistics Section
if db:
    st.divider()
    st.subheader("📊 Color Statistics (All Data)")
    
    if st.button("🔍 View Color Statistics", type="secondary"):
        with st.spinner("Loading color statistics..."):
            color_counts = db.get_color_counts()
            
            if color_counts:
                # Create DataFrame for visualization
                import pandas as pd
                color_df = pd.DataFrame(list(color_counts.items()), columns=['Color', 'Count'])
                
                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Colors", len(color_counts))
                with col2:
                    st.metric("Total Entries", sum(color_counts.values()))
                
                # Bar chart
                st.bar_chart(color_df.set_index('Color'))
                
                # Also show as table
                with st.expander("View detailed color counts"):
                    st.dataframe(color_df, use_container_width=True)
            else:
                st.warning("No data found in database. Please ensure data was saved successfully.")
                st.info("Tip: Check that you clicked 'Process and Normalize Data' button after uploading CSV files.")

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About this app")
    st.markdown("""
    ### Data Requirements
    Tu archivo CSV puede estar en cualquiera de estos 3 formatos:
    
    **Formato 1:** Lastname, Firstname, phonenumber, color, zipcode
    
    **Formato 2:** Firstname Lastname, color, zipcode, phonenumber
    
    **Formato 3:** Firstname, Lastname, zipcode, phonenumber, color
    
    Todos los formatos serán detectados y normalizados automáticamente.
    
    ### Normalización
    1. Los números de teléfono se normalizan al formato xxx-xxx-xxxx
    2. Las entradas inválidas son identificadas en la sección de error.
    3. Los resultados se ordenan por apellido y luego por nombre
    4. La salida se guarda con identación de 2 espacios y claves ordenadas (lastname, firstname)
    
    ### Database Tables
    Nuestra base de datos PostgreSQL contiene dos tablas principales:
    - **original_data**: Almacena los datos CSV sin procesar
    - **normalized_data**: Almacena las entradas normalizadas

    ### Color summarization
    La sección de estadísticas de color muestra un resumen de todos los colores en la base de datos, junto con sus recuentos.
    """)
    
    st.divider()
    
    st.markdown("### Database Status")
    if db:
        st.success("Connected")
    else:
        st.error("Not Connected")

