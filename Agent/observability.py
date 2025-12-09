import logging
import json
import os
from datetime import datetime

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "agent.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Observability:
    @staticmethod
    def log_step(step_name: str, input_data: dict, output_data: dict):
        """Logs a step in the agent execution."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "input": str(input_data),
            "output": str(output_data)
        }
        logging.info(json.dumps(log_entry))

    @staticmethod
    def save_rating(run_id: str, rating: int, comment: str = ""):
        """Saves a user rating for a run."""
        rating_file = os.path.join(log_dir, "ratings.json")
        entry = {
            "run_id": run_id,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        
        ratings = []
        if os.path.exists(rating_file):
            with open(rating_file, "r") as f:
                try:
                    ratings = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        ratings.append(entry)
        
        with open(rating_file, "w") as f:
            json.dump(ratings, f, indent=2)
