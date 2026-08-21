import json
import requests
from pathlib import Path
from ingestion import NYC311Ingestion

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "tests" / "api_data_sample" / "sample_records_1000.json"
RECORD_LIMIT = 1000

def fetch_latest_records(limit: int = RECORD_LIMIT) -> list[dict]:
	ingestion = NYC311Ingestion(batch_size=limit)
	ingestion.session = requests.Session()
	try:
		return ingestion.extract_batch(
			limit=limit,
			override_params={
				"$order": "created_date DESC, unique_key DESC",
			},
		)
	finally:
		ingestion.session.close()

def write_sample(records: list[dict], output_path: Path = OUTPUT_PATH) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

def main() -> None:
	records = fetch_latest_records()
	write_sample(records)
	print(f"Wrote {len(records)} records to {OUTPUT_PATH}")

if __name__ == "__main__":
	main()
