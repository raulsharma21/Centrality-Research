import pandas as pd
from datetime import datetime
import os

def preprocess_eth_blocks_csv(input_file, output_file):
    """
    Preprocess ETH blocks CSV:
    1. Remove duplicates based on Block number
    2. Extract Date from DateTime (UTC) 
    3. Clean and validate data
    4. Save to new file
    """
    
    print(f"Loading CSV file: {input_file}")
    
    try:
        # Load CSV with pandas
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df)} rows")
        
        # Show original columns
        print(f"Original columns: {list(df.columns)}")
        
        # Check for DateTime (UTC) column
        if 'DateTime (UTC)' not in df.columns:
            print("❌ 'DateTime (UTC)' column not found!")
            return False
            
        # Check for Block column
        if 'Block' not in df.columns:
            print("❌ 'Block' column not found!")
            return False
        
        print(f"Date range: {df['DateTime (UTC)'].min()} to {df['DateTime (UTC)'].max()}")
        
        # Remove duplicates based on Block number (primary key)
        initial_count = len(df)
        df = df.drop_duplicates(subset=['Block'], keep='first')
        duplicates_removed = initial_count - len(df)
        print(f"✅ Removed {duplicates_removed} duplicate blocks")
        
        # Extract Date from DateTime (UTC)
        print("Extracting dates from DateTime (UTC)...")
        df['Date'] = pd.to_datetime(df['DateTime (UTC)']).dt.strftime('%Y-%m-%d')
        
        # Validate dates were extracted correctly
        print(f"✅ Date extraction complete. Unique dates: {df['Date'].nunique()}")
        print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        # Clean numeric columns (remove commas)
        numeric_columns = ['Block', 'Slot', 'Epoch', 'Txn', 'Gas Used', 'Gas Limit']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '')
        
        # Remove rows with invalid Block numbers
        initial_count = len(df)
        df = df[pd.to_numeric(df['Block'], errors='coerce').notna()]
        invalid_blocks = initial_count - len(df)
        if invalid_blocks > 0:
            print(f"⚠️  Removed {invalid_blocks} rows with invalid block numbers")
        
        # Reorder columns to put keys first
        cols = df.columns.tolist()
        # Move Date and Block to front
        if 'Date' in cols:
            cols.remove('Date')
        if 'Block' in cols:
            cols.remove('Block')
        df = df[['Date', 'Block'] + cols]
        
        # Save processed file
        df.to_csv(output_file, index=False)
        print(f"✅ Processed file saved: {output_file}")
        print(f"Final record count: {len(df)}")
        
        # Show sample of processed data
        print("\nSample of processed data:")
        print(df[['Date', 'Block', 'DateTime (UTC)', 'Fee Recipient']].head())
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        return False

def validate_processed_file(file_path):
    """Validate the processed file for common issues"""
    try:
        df = pd.read_csv(file_path)
        
        print(f"\n=== Validation Results ===")
        print(f"Total records: {len(df)}")
        print(f"Unique blocks: {df['Block'].nunique()}")
        print(f"Unique dates: {df['Date'].nunique()}")
        
        # Check for missing required fields
        missing_dates = df['Date'].isna().sum()
        missing_blocks = df['Block'].isna().sum()
        
        if missing_dates > 0:
            print(f"⚠️  {missing_dates} rows missing Date")
        if missing_blocks > 0:
            print(f"⚠️  {missing_blocks} rows missing Block")
            
        # Check date format
        try:
            pd.to_datetime(df['Date'].dropna())
            print(f"✅ All dates are valid format")
        except:
            print(f"❌ Some dates have invalid format")
            
        # Show data distribution
        print(f"\nRecords per date (top 10):")
        print(df['Date'].value_counts().head(10))
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "ETH_Block_Data_Cleaned.csv"
    output_file = "ETH_Block_Data_Processed.csv"
    
    print("=== ETH Blocks CSV Preprocessing ===")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        exit(1)
    
    # Preprocess the file
    if preprocess_eth_blocks_csv(input_file, output_file):
        print(f"\n=== Preprocessing completed successfully! ===")
        
        # Validate the processed file
        validate_processed_file(output_file)
        
        print(f"\n🎉 Ready for DynamoDB upload: {output_file}")
    else:
        print(f"❌ Preprocessing failed")