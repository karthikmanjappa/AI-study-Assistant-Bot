 
from google import genai
import dotenv

dotenv.load_dotenv()

client = genai.Client(api_key="AQ.Ab8RN6ILHKo1L1dvrWFCtJgaGpd-s3NQrTJY3uxvuFtrAHM6vw")

for m in client.models.list():
    print(m.name)