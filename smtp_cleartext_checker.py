import argparse
import socket
import json
import pandas as pd
import csv
from tqdm import tqdm

# Banner
BANNER = """
############################################
#   SMTP Cleartext Login Permitted Tester  #
#         Developed by Afif                #
############################################
"""

def check_smtp_cleartext_login(host, port, timeout=5):
    """Tests if the SMTP server allows cleartext login"""
    result = {
        "host": host,
        "port": port,
        "status": "Failed",
        "banner": None,
        "cleartext_login_permitted": False
    }
    
    try:
        with socket.create_connection((host, port), timeout) as sock:
            sock.recv(1024)  # Read initial SMTP banner
            sock.sendall(b"EHLO test\r\n")
            response = sock.recv(1024).decode(errors='ignore')
            result["banner"] = response.strip()

            if "250" in response and "AUTH" in response:
                if "PLAIN" in response or "LOGIN" in response:
                    result["cleartext_login_permitted"] = True
                    result["status"] = "Vulnerable"
                else:
                    result["status"] = "Secure"
            else:
                result["status"] = "Unknown"

    except Exception as e:
        result["status"] = f"Error: {str(e)}"

    return result

def save_results(results, output_file, output_format):
    """Saves results in the specified format"""
    if output_format == "json":
        with open(output_file, "w") as f:
            json.dump(results, f, indent=4)
    elif output_format == "csv":
        keys = results[0].keys()
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
    elif output_format == "xlsx":
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
    elif output_format == "txt":
        with open(output_file, "w") as f:
            for res in results:
                f.write(json.dumps(res) + "\n")

def parse_bulk_target(line):
    """Parses host and port from bulk input"""
    if ":" not in line:
        raise ValueError(f"Invalid format in bulk mode: '{line}'. Use 'host:port'.")
    host, port = line.split(":")
    return host.strip(), int(port.strip())

def main():
    print(BANNER)
    
    parser = argparse.ArgumentParser(description="SMTP Cleartext Login Permitted Tester")
    parser.add_argument("target", help="Single host or file containing list of hosts (bulk mode)")
    parser.add_argument("--port", type=int, help="SMTP port (used only in single mode, default: 25)")
    parser.add_argument("--bulk", action="store_true", help="Enable bulk mode (requires file input)")
    parser.add_argument("--output", help="File to save results (format: csv, xlsx, txt, json)")

    args = parser.parse_args()
    
    targets = []
    
    if args.bulk:
        # Bulk mode: Read file containing "host:port"
        try:
            with open(args.target, "r") as file:
                targets = [parse_bulk_target(line.strip()) for line in file if line.strip()]
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        # Single mode: Use CLI argument with optional --port
        port = args.port if args.port else 25  # Default port 25 if not provided
        targets.append((args.target, port))

    results = []
    
    print(f"\nScanning {len(targets)} target(s)...\n")
    for host, port in tqdm(targets, desc="Checking SMTP", unit="host"):
        result = check_smtp_cleartext_login(host, port)
        results.append(result)

    # Print results to CLI in JSON format if no output file is specified
    if not args.output:
        print(json.dumps(results, indent=4))
    else:
        output_format = args.output.split(".")[-1]
        if output_format not in ["csv", "xlsx", "txt", "json"]:
            print("Unsupported output format! Use csv, xlsx, txt, or json.")
            return
        save_results(results, args.output, output_format)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
