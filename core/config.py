RAW_DATA_DIR = "data/raw/"
CLEAN_DATA_DIR = "data/clean/"
EVAL_RESULTS_DATA_DIR = "data/eval/results"

MARKET_AGGREGATE_CSV = "aggregate_job_postings_US.csv"
MARKET_SECTOR_CSV = "job_postings_by_sector_US.csv"
MARKET_JOB_POSTINGS_SOURCE_BASE_URL = (
    "https://raw.githubusercontent.com/hiring-lab/job_postings_tracker/master/US/"
)

UPSERT_BATCH_SIZE = 1000

AGGREGATE_TABLE_NAME = "job_postings_aggregate"
SECTOR_TABLE_NAME = "job_postings_by_sector"
HN_JOB_POSTING_TABLE_NAME = "hn_job_postings"

HN_API_BASE_URL = "https://hn.algolia.com/api/v1/"
HN_JOBS_FILENAME = "hn_jobs.json"
HN_RAW_DATA_PATH = "data/raw/"

OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-4o-mini"


RAGAS_FILENAME_TEMPLATE = "ragas_{timestamp}.csv"


SCORE_DIMENSIONS = ("skills_match", "seniority_match", "domain_match", "logistics_match")

SCORE_WEIGHTS = {
    "skills_match": 0.40,
    "seniority_match": 0.25,
    "domain_match": 0.20,
    "logistics_match": 0.15,
}

THRESHOLD_BANDS = (
    (4.0, "strong"),
    (2.5, "moderate"),
    (0.0, "weak"),
)

PROFILE_FIELDS = ("skills", "domain", "logistics")

SCORE_MAX_CANDIDATES = 5

MIN_YEARS = 0
MAX_YEARS = 50
