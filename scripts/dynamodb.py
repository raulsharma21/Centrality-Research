import boto3
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

table_name = 'ETH_Blocks'

# DynamoDB client with credentials from environment variables
dynamodb = boto3.client(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),  # Fixed: was AWS_SECRET_KEY
    region_name='us-west-1'
)

def extract_date_from_datetime(datetime_str):
    """Extract date string from datetime for use as partition key"""
    try:
        # Parse the datetime string
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        # Return just the date part
        return dt.strftime("%Y-%m-%d")
    except ValueError as e:
        print(f"Error parsing datetime: {e}")
        return None

def convert_csv_row_to_dynamodb_item(row):
    """Convert a CSV row to DynamoDB item format"""
    
    # Extract date for partition key
    date_key = extract_date_from_datetime(row['DateTime (UTC)'])
    if not date_key:
        return None
    
    # Build DynamoDB item
    item = {
        'Date': {'S': date_key},  # Partition key
        'Block': {'N': str(row['Block'])},  # Sort key
        'DateTime (UTC)': {'S': row['DateTime (UTC)']},
    }
    
    # Add other fields, handling empty values
    field_mappings = {
        'Slot': 'N',
        'Epoch': 'N', 
        'BlobCount': 'S',
        'Txn': 'N',
        'Fee Recipient': 'S',
        'Fee Recipient Nametag': 'S',
        'Gas Used': 'N',
        'Gas Used(%)': 'S',
        ' % Of Gas Target': 'S',
        'Gas Limit': 'N',
        'Base Fee': 'S',
        'Reward': 'S',
        'Burnt Fees (ETH)': 'N',
        'Burnt Fees (%)': 'S'
    }
    
    for field, data_type in field_mappings.items():
        value = row.get(field, '').strip()
        
        if not value:  # Empty value
            item[field] = {'NULL': True}
        elif data_type == 'N':  # Number
            # Remove commas and convert to string for DynamoDB
            clean_value = value.replace(',', '')
            try:
                float(clean_value)  # Validate it's a number
                item[field] = {'N': clean_value}
            except ValueError:
                item[field] = {'NULL': True}
        else:  # String
            item[field] = {'S': value}
    
    return item

def load_and_upload_first_record(file_path):
    """Load CSV file and upload the first record to DynamoDB"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Get the first row
            first_row = next(csv_reader)
            print(f"First row from CSV: {first_row}")
            
            # Convert to DynamoDB format
            dynamodb_item = convert_csv_row_to_dynamodb_item(first_row)
            
            if dynamodb_item:
                # Upload to DynamoDB
                response = dynamodb.put_item(
                    TableName=table_name,
                    Item=dynamodb_item
                )
                print(f"✅ Item added successfully!")
                print(f"Partition key (Date): {dynamodb_item['Date']['S']}")
                print(f"Sort key (Block): {dynamodb_item['Block']['N']}")
                print(f"Response: {response['ResponseMetadata']['HTTPStatusCode']}")
                
            else:
                print("❌ Failed to convert CSV row to DynamoDB item")
                
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")

if __name__ == "__main__":
    # Load CSV file and upload first record
    csv_file_path = "../data/raw/ETH_Block_Data_Cleaned.csv"
    load_and_upload_first_record(csv_file_path)