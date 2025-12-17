import boto3
import os
import csv
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

table_name = 'ETH_Blocks'

# DynamoDB client with credentials from environment variables
dynamodb = boto3.client(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-west-1'
)

def convert_csv_row_to_dynamodb_item(row):
    """Convert a CSV row to DynamoDB item format"""
    
    # Build DynamoDB item with required keys first
    item = {
        'Date': {'S': str(row['Date'])},  # Partition key (already processed)
        'Block': {'N': str(row['Block'])},  # Sort key
    }
    
    # Add other fields, handling empty values
    field_mappings = {
        'DateTime (UTC)': 'S',
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
        if field not in row:
            continue
            
        value = str(row[field]).strip()
        
        if not value or value.lower() in ['', 'nan', 'null', 'none']:  # Empty value
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

def batch_upload_to_dynamodb(csv_file_path, batch_size=25, max_records=None):
    """
    Upload CSV data to DynamoDB using batch operations
    DynamoDB batch_write_item supports max 25 items per batch
    """
    
    total_uploaded = 0
    batch_count = 0
    failed_items = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            batch_items = []
            
            print(f"Starting batch upload to DynamoDB table: {table_name}")
            print(f"Batch size: {batch_size} items per batch")
            
            for i, row in enumerate(csv_reader):
                
                # Convert row to DynamoDB format
                dynamodb_item = convert_csv_row_to_dynamodb_item(row)
                
                if dynamodb_item:
                    batch_items.append({
                        'PutRequest': {
                            'Item': dynamodb_item
                        }
                    })
                
                # When batch is full or we've reached the end
                if len(batch_items) >= batch_size:
                    success = upload_batch(batch_items, batch_count)
                    if success:
                        total_uploaded += len(batch_items)
                        batch_count += 1
                        
                        # Progress update every 10 batches (250 records)
                        if batch_count % 10 == 0:
                            print(f"Progress: {total_uploaded:,} records uploaded ({batch_count} batches)")
                    else:
                        failed_items.extend(batch_items)
                    
                    batch_items = []  # Reset batch
                
                # Optional: limit for testing
                if max_records and i >= max_records - 1:
                    print(f"Reached max_records limit: {max_records}")
                    break
            
            # Upload remaining items in the last batch
            if batch_items:
                success = upload_batch(batch_items, batch_count)
                if success:
                    total_uploaded += len(batch_items)
                    batch_count += 1
                else:
                    failed_items.extend(batch_items)
        
        print(f"\n=== Upload Complete ===")
        print(f"Total records uploaded: {total_uploaded:,}")
        print(f"Total batches: {batch_count}")
        print(f"Failed items: {len(failed_items)}")
        
        if failed_items:
            print(f"⚠️  Some items failed to upload. Consider retrying failed items.")
            
        return total_uploaded, failed_items
        
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file_path}")
        return 0, []
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")
        return total_uploaded, failed_items

def upload_batch(batch_items, batch_number):
    """Upload a single batch to DynamoDB with retry logic"""
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            response = dynamodb.batch_write_item(
                RequestItems={
                    table_name: batch_items
                }
            )
            
            # Check for unprocessed items
            unprocessed = response.get('UnprocessedItems', {})
            if unprocessed:
                print(f"⚠️  Batch {batch_number}: {len(unprocessed.get(table_name, []))} unprocessed items")
                # Could implement retry logic for unprocessed items here
            
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Batch {batch_number} failed (attempt {attempt + 1}), retrying in {retry_delay}s: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"❌ Batch {batch_number} failed after {max_retries} attempts: {str(e)}")
                return False
    
    return False

def estimate_upload_time(csv_file_path, batch_size=25):
    """Estimate upload time based on file size"""
    try:
        with open(csv_file_path, 'r') as file:
            row_count = sum(1 for line in file) - 1  # Subtract header
        
        batches_needed = (row_count + batch_size - 1) // batch_size
        # Estimate ~0.1 seconds per batch (conservative)
        estimated_minutes = (batches_needed * 0.1) / 60
        
        print(f"=== Upload Estimation ===")
        print(f"Total records: {row_count:,}")
        print(f"Batches needed: {batches_needed:,}")
        print(f"Estimated time: {estimated_minutes:.1f} minutes")
        
        return row_count, batches_needed, estimated_minutes
        
    except Exception as e:
        print(f"Error estimating upload time: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    csv_file_path = "../data/raw/ETH_Block_Data_Processed.csv"
    
    # Check if processed file exists
    if not os.path.exists(csv_file_path):
        print(f"❌ Processed file not found: {csv_file_path}")
        print("Please run the preprocessing script first!")
        exit(1)
    
    print("=== DynamoDB Bulk Upload ===")
    
    # Estimate upload time
    row_count, batches, est_time = estimate_upload_time(csv_file_path)
    
    if row_count == 0:
        exit(1)
    
    # Ask for confirmation for large uploads
    if row_count > 10000:
        response = input(f"\nReady to upload {row_count:,} records? This will take ~{est_time:.1f} minutes. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Upload cancelled.")
            exit(0)
    
    # For testing, you can limit the number of records
    # max_records = 100  # Uncomment to test with first 100 records
    max_records = None  # Upload all records
    
    # Start upload
    start_time = time.time()
    uploaded, failed = batch_upload_to_dynamodb(csv_file_path, max_records=max_records)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\n🎉 Upload completed in {duration/60:.1f} minutes")
    print(f"Records per second: {uploaded/duration:.1f}")
    
    if uploaded > 0:
        print(f"✅ Successfully uploaded {uploaded:,} records to DynamoDB!")
    else:
        print(f"❌ No records were uploaded.")