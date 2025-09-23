import time
import random
import string
from datetime import datetime

def generate_random_string(length=10):
    """Generate a random alphanumeric string of given length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    # Generate and store random string
    random_str = generate_random_string(12)
    print(f"{random_str}")

    # Loop to print with timestamp
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] {random_str}")
        time.sleep(5)

if __name__ == "__main__":
    main()
