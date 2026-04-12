import uuid
import base64
import argparse
import re

def get_mac_address():
    """Returns the MAC address in XX:XX:XX:XX:XX:XX format."""
    return ':'.join(re.findall('..', '%012x' % uuid.getnode()))

def generate_license_key():
    """Generates a license key based on the machine's MAC address."""
    machine_id = get_mac_address()

    # Base32 encoding of the MAC address
    raw_key = base64.b32encode(machine_id.encode()).decode().rstrip("=")

    # Format into blocks of 5 characters
    blocks = [raw_key[i:i+5] for i in range(0, len(raw_key), 5)]
    return "-".join(blocks)

def verify_license_key(provided_key):
    """Verifies if the provided key matches the one generated for this machine."""
    # Remove dashes and normalize to uppercase for comparison
    normalized_provided = provided_key.replace("-", "").upper()

    expected_key = generate_license_key().replace("-", "")

    return normalized_provided == expected_key

def main():
    parser = argparse.ArgumentParser(description="Machine-bound License Key Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    subparsers.add_parser("generate", help="Generate a license key for this machine")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a license key")
    verify_parser.add_argument("key", help="The license key to verify")

    args = parser.parse_args()

    if args.command == "generate":
        key = generate_license_key()
        print(f"Machine ID (MAC): {get_mac_address()}")
        print(f"License Key:      {key}")
    elif args.command == "verify":
        if verify_license_key(args.key):
            print("✅ License key is valid for this machine.")
        else:
            print("❌ Invalid license key for this machine.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
