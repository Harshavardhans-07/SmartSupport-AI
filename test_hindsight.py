
import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

bank_id = os.getenv("HINDSIGHT_BANK_ID")

try:
    print("Connecting to Hindsight...")

    # Store a sample customer memory
    client.retain(
        bank_id=bank_id,
        content="Customer Alex prefers email support and reported a delayed delivery."
    )

    print("Customer memory stored successfully!")

    # Recall the stored memory
    result = client.recall(
        bank_id=bank_id,
        query="What does Alex prefer for customer support?"
    )

    print("\nRecalled memories:")
    for memory in result.results:
        print("-", memory.text)

except Exception as e:
    print("Hindsight error:", e)

finally:
    client.close()
