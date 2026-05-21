import pandas as pd

from core.config import AGGREGATE_CSV, CLEAN_DATA_DIR, RAW_DATA_DIR, SECTOR_CSV


def clean_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    df['date'] = pd.to_datetime(df['date'])
    df.columns = ['date', 'job_country', 'index_sa', 'index_nsa', 'variable']
    df = df.dropna()
    df = df.drop_duplicates(subset=['date', 'job_country', 'variable'])
    return df

def clean_sector(df: pd.DataFrame) -> pd.DataFrame:
    df['date'] = pd.to_datetime(df['date'])
    df.columns = ['date', 'job_country', 'index_value', 'variable', 'sector_name']
    df = df.dropna()
    df = df.drop_duplicates(subset=['date', 'job_country', 'sector_name', 'variable'])
    return df


def process_aggregate() -> None:
    print("=========== Aggregate Begin ==========")
    
    df = pd.read_csv(RAW_DATA_DIR + AGGREGATE_CSV) 
    
    print(f"Raw shape {df.shape}")
    df = clean_aggregate(df)
    print(f"Clean shape {df.shape}")
    
    df.to_csv(CLEAN_DATA_DIR + AGGREGATE_CSV, index=False)
    
    print("=========== Aggregate Done ==========")
    
def process_sector() -> None:
    print("=========== Sector Begin ==========")
    
    df = pd.read_csv(RAW_DATA_DIR + SECTOR_CSV) 
    
    print(f"Raw shape {df.shape}")
    df = clean_sector(df)
    print(f"Clean shape {df.shape}")
    
    df.to_csv(CLEAN_DATA_DIR + SECTOR_CSV, index=False)
    
    print ("=========== Sector Done ==========")
   

def main() -> None:
    process_aggregate()
    process_sector()

if __name__ == '__main__':
    main()