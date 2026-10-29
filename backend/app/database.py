import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.config import settings

logger = logging.getLogger("url_shortener.database")

# In-memory mock store for local offline testing
_mock_storage: Dict[str, Dict[str, Any]] = {}


class DatabaseManager:
    """Manages DynamoDB operations with automatic IAM role credential resolution

    and optional local in-memory fallback for testing.
    """

    def __init__(self):
        self.table = None
        self.is_mock = settings.use_mock_db
        self._initialize()

    def _initialize(self):
        if self.is_mock:
            logger.warning("Using in-memory mock storage (USE_MOCK_DB=true).")
            return

        try:
            dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
            self.table = dynamodb.Table(settings.dynamodb_table)
            logger.info(
                f"Connected to DynamoDB table '{settings.dynamodb_table}' in region '{settings.aws_region}'"
            )
        except NoCredentialsError:
            logger.warning(
                "No AWS credentials found. Falling back to in-memory mock storage for local testing."
            )
            self.is_mock = True
        except Exception as e:
            logger.error(f"Error initializing DynamoDB resource: {e}")
            if settings.use_mock_db:
                self.is_mock = True
            else:
                raise

    def save_url(self, short_code: str, original_url: str, created_at: str) -> Dict[str, Any]:
        """Saves a shortened link item to DynamoDB (or mock storage)."""
        item = {
            "short_code": short_code,
            "original_url": original_url,
            "created_at": created_at,
        }

        if self.is_mock:
            _mock_storage[short_code] = item
            logger.info(f"[MOCK DB] Saved: {short_code} -> {original_url}")
            return item

        try:
            self.table.put_item(Item=item)
            logger.info(f"[DynamoDB] Saved item: {short_code} -> {original_url}")
            return item
        except ClientError as e:
            logger.error(f"DynamoDB ClientError on put_item: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving item to DynamoDB: {e}")
            raise

    def get_url(self, short_code: str) -> Optional[Dict[str, Any]]:
        """Retrieves a shortened link item by short_code from DynamoDB (or mock storage)."""
        if self.is_mock:
            item = _mock_storage.get(short_code)
            logger.info(f"[MOCK DB] Get {short_code}: {'Found' if item else 'Not Found'}")
            return item

        try:
            response = self.table.get_item(Key={"short_code": short_code})
            item = response.get("Item")
            logger.info(f"[DynamoDB] Get {short_code}: {'Found' if item else 'Not Found'}")
            return item
        except ClientError as e:
            logger.error(f"DynamoDB ClientError on get_item: {e.response['Error']['Message']}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching item from DynamoDB: {e}")
            raise

    def is_connected(self) -> bool:
        """Checks if the DynamoDB table is accessible or running in mock mode."""
        if self.is_mock:
            return True
        try:
            self.table.load()
            return True
        except Exception:
            return False


db = DatabaseManager()
