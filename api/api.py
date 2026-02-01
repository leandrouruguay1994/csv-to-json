from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import pandas as pd
import json
import io
from datetime import datetime

import sys
sys.path.append('/app')

from app.utils.database import DatabaseManager
from app.utils.normalizer import DataNormalizer

app = FastAPI(
    title="Streaver API",
    description="API for CSV normalization and data management",
    version="1.0.0"
)

# Initialize database connection
def get_db():
    """Get database connection"""
    db = DatabaseManager()
    if db.connect():
        db.create_tables()
        return db
    return None

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Streaver API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    db = get_db()
    if db:
        db.close()
        return {"status": "healthy", "database": "connected"}
    return {"status": "unhealthy", "database": "disconnected"}

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload and process CSV file
    
    Accepts CSV in 3 formats:
    1. Lastname, Firstname, phonenumber, color, zipcode
    2. Firstname Lastname, color, zipcode, phonenumber
    3. Firstname, Lastname, zipcode, phonenumber, color
    """
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Replace NaN with None for JSON compatibility
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notna(df), None)
        
        print(f"API: CSV read successfully, {len(df)} rows")
        
        # Convert to original data format
        original_data = df.to_dict('records')
        
        # Process and normalize
        entries, errors = DataNormalizer.process_csv_data(df)
        
        print(f"API: Processed {len(entries)} entries, {len(errors)} errors")
        
        # Save to database
        db = get_db()
        if db:
            print("API: Database connected")
            try:
                original_id = db.insert_original_data(original_data)
                print(f"API: Original data inserted with ID: {original_id}")
                
                if original_id and entries:
                    success = db.insert_normalized_data(entries, original_id)
                    print(f"API: Normalized data insert result: {success}")
                    if not success:
                        print("API: ERROR - Failed to insert normalized data")
                else:
                    print(f"API: Skipping normalized insert - original_id={original_id}, entries={len(entries)}")
                db.close()
            except Exception as e:
                print(f"API: Database error: {e}")
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Database error: {str(e)}"}
                )
        else:
            print("API: ERROR - Database connection failed")
        
        # Create result
        result = {
            "entries": entries,
            "errors": errors
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"API: Processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
