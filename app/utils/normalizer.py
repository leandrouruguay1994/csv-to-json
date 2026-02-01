import re
from typing import List, Dict, Tuple

class DataNormalizer:
    """Handles CSV data normalization according to specified rules"""
    
    @staticmethod
    def normalize_phone(phone_str: str) -> str:
        """
        Normalize phone number to xxx-xxx-xxxx format
        Extracts digits and formats them
        """
        if not phone_str:
            return None
        
        # Extract all digits from the phone string
        digits = re.sub(r'\D', '', str(phone_str))
        
        # Check if we have exactly 10 digits
        if len(digits) == 10:
            return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':
            # Handle case where number starts with country code 1
            return f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        else:
            # Invalid phone number
            return None
    
    @staticmethod
    def validate_zip(zip_str: str) -> str:
        """
        Validate and normalize ZIP code
        Accept only 5-digit format
        """
        if not zip_str:
            return None
        
        zip_clean = str(zip_str).strip()
        
        # Check for 5-digit ZIP
        if re.match(r'^\d{5}$', zip_clean):
            return zip_clean
        
        # Check if it's just digits that could be a ZIP
        digits = re.sub(r'\D', '', zip_clean)
        if len(digits) == 5:
            return digits
        
        return None
    
    @staticmethod
    def detect_format(df) -> int:
        """
        Detect which CSV format is being used
        Returns: 1, 2, or 3 based on the format detected
        """
        columns = [col.strip().lower() for col in df.columns]
        
        # Format 1: Lastname, Firstname, phonenumber, color, zipcode
        if 'lastname' in columns and 'firstname' in columns and columns.index('lastname') < columns.index('firstname'):
            return 1
        
        # Format 2: Firstname Lastname (combined), color, zipcode, phonenumber
        # Check for a column that might contain full names
        for col in df.columns:
            if col.strip().lower() not in ['color', 'zipcode', 'phonenumber', 'zip', 'phone']:
                # Could be the full name column
                sample_value = str(df[col].iloc[0]) if len(df) > 0 else ''
                if ' ' in sample_value:
                    return 2
        
        # Format 3: Firstname, Lastname, zipcode, phonenumber, color (default)
        return 3
    
    @staticmethod
    def process_csv_data(df) -> Tuple[List[Dict], List[int]]:
        """
        Process CSV data and return normalized entries and error line numbers
        Supports 3 different CSV formats
        
        Args:
            df: pandas DataFrame containing the CSV data
            
        Returns:
            Tuple of (entries list, errors list)
        """
        entries = []
        errors = []
        
        # Detect format
        csv_format = DataNormalizer.detect_format(df)
        
        for idx, row in df.iterrows():
            try:
                firstname = ''
                lastname = ''
                phone = ''
                zip_code = ''
                color = ''
                
                # Parse based on format
                if csv_format == 1:
                    # Format 1: Lastname, Firstname, phonenumber, color, zipcode
                    lastname = str(row.iloc[0]).strip() if len(row) > 0 else ''
                    firstname = str(row.iloc[1]).strip() if len(row) > 1 else ''
                    phone = row.iloc[2] if len(row) > 2 else ''
                    color = str(row.iloc[3]).strip() if len(row) > 3 else ''
                    zip_code = row.iloc[4] if len(row) > 4 else ''
                    
                elif csv_format == 2:
                    # Format 2: Firstname Lastname, color, zipcode, phonenumber
                    fullname = str(row.iloc[0]).strip() if len(row) > 0 else ''
                    name_parts = fullname.split(' ', 1)
                    firstname = name_parts[0] if len(name_parts) > 0 else ''
                    lastname = name_parts[1] if len(name_parts) > 1 else ''
                    color = str(row.iloc[1]).strip() if len(row) > 1 else ''
                    zip_code = row.iloc[2] if len(row) > 2 else ''
                    phone = row.iloc[3] if len(row) > 3 else ''
                    
                else:
                    # Format 3: Firstname, Lastname, zipcode, phonenumber, color
                    firstname = str(row.iloc[0]).strip() if len(row) > 0 else ''
                    lastname = str(row.iloc[1]).strip() if len(row) > 1 else ''
                    zip_code = row.iloc[2] if len(row) > 2 else ''
                    phone = row.iloc[3] if len(row) > 3 else ''
                    color = str(row.iloc[4]).strip() if len(row) > 4 else ''
                
                # Validate required fields
                if not firstname or not lastname:
                    errors.append(idx)
                    continue
                
                # Normalize phone number
                normalized_phone = DataNormalizer.normalize_phone(phone)
                if not normalized_phone:
                    errors.append(idx)
                    continue
                
                # Validate ZIP code
                normalized_zip = DataNormalizer.validate_zip(zip_code)
                if not normalized_zip:
                    errors.append(idx)
                    continue
                
                # Validate color (optional but if present must not be empty)
                if not color:
                    errors.append(idx)
                    continue
                
                # Add successfully processed entry
                entries.append({
                    'firstname': firstname,
                    'lastname': lastname,
                    'phonenumber': normalized_phone,
                    'zipcode': normalized_zip,
                    'color': color
                })
                
            except Exception as e:
                # If any error occurs processing this line, add to errors
                errors.append(idx)
        
        # Sort entries by lastname, then firstname (ascending alphabetical order)
        entries.sort(key=lambda x: (x['lastname'].lower(), x['firstname'].lower()))
        
        return entries, errors
