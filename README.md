# SMTP Cleartext Login Permitted Tester

## Overview
This script checks whether an SMTP server offers cleartext authentication (`AUTH PLAIN` or `AUTH LOGIN`) on an unencrypted connection, which lets credentials be sniffed on the network.

- Single and bulk mode: test one host or a list of hosts from a file.
- Default ports: if no port is given, each host is checked on 25, 587 and 465.
- Multithreaded: hosts are checked in parallel, so large lists finish fast with low CPU usage.
- Port 465 support: connects with implicit TLS, the way real clients do.
- Flexible input: accepts `host`, `host:port`, and full URLs like `ftp://host/` or `https://host:8443/path`.
- Output formats: JSON (default, printed to CLI), CSV, XLSX, TXT.

---

## Installation
```bash
pip install tqdm pandas openpyxl
```
`pandas` and `openpyxl` are only needed for XLSX output.

Clone the repository:
```bash
git clone https://github.com/threatlabindonesia/smtp_cleartext_checker.git
cd smtp_cleartext_checker
```

---

## Usage

### Options
| Option | Description |
|---|---|
| `target` | A single host, or a file with a list of hosts (with `--bulk`) |
| `--port` | Port for single mode. If omitted, 25, 587 and 465 are all checked |
| `--bulk` | Read targets from a file |
| `--output` | Save results to a file. Format is taken from the extension: `.csv`, `.xlsx`, `.txt`, `.json` |
| `--threads` | Number of parallel checks (default: 20) |
| `--timeout` | Timeout per connection in seconds (default: 5) |

### 1. Single check
```bash
# Check ports 25, 587 and 465
python3 smtp_cleartext_checker.py smtp.example.com

# Check one specific port
python3 smtp_cleartext_checker.py smtp.example.com --port 587
```

### 2. Bulk check
Create a file such as `targets.txt`. Each line can be any of these:
```
example.com
mail.example.org:2525
ftp://ftp.example.net/
https://web.example.com:8443/login
# lines starting with # are ignored
```

How each line is read:
- `example.com` is checked on 25, 587 and 465.
- `mail.example.org:2525` is checked only on 2525.
- URLs have the scheme, path and `user@` removed. If the URL has a port, only that port is checked.
- Empty lines, comments and duplicates are skipped.
- Invalid lines are skipped with a `[skip]` message instead of stopping the scan.

Run:
```bash
python3 smtp_cleartext_checker.py targets.txt --bulk
```

### 3. Saving results
```bash
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.csv
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.xlsx
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.txt
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.json
```

### 4. Performance tuning
The scan spends almost all its time waiting on the network, not on the CPU, so more threads means a faster scan without much extra CPU load.

```bash
python3 smtp_cleartext_checker.py targets.txt --bulk --threads 10 --timeout 3 --output results.xlsx
```
- On a slow connection or small machine, use `--threads 10`.
- Dead hosts take the longest, so a lower `--timeout` (3 to 4) speeds up big lists.

---

## Output Format (JSON Example)
```json
[
    {
        "host": "smtp.vulnerable.com",
        "port": 25,
        "status": "Vulnerable",
        "banner": "250-smtp.vulnerable.com Hello test\n250-AUTH PLAIN LOGIN\n250 HELP",
        "cleartext_login_permitted": true
    }
]
```
Results are sorted by host, then port.

### Output fields
| Field | Description |
|---|---|
| `host` | The SMTP server tested |
| `port` | The port tested |
| `status` | Result of the check (see below) |
| `banner` | The full server response to `EHLO test` |
| `cleartext_login_permitted` | `true` if `AUTH PLAIN` or `AUTH LOGIN` is offered on an unencrypted connection |

---

## How Detection Works
1. The script connects to the server. On port 465 it starts TLS first. On every other port it connects in plaintext.
2. It reads the full greeting, sends `EHLO test`, and reads the full multi-line response.
3. It sets the status:

| Status | Meaning |
|---|---|
| `Vulnerable` | Plaintext connection, and the server offers `AUTH PLAIN` or `AUTH LOGIN` before any encryption |
| `Secure` | Plaintext connection, and `AUTH` is offered but without `PLAIN` or `LOGIN` |
| `Secure (implicit TLS)` | Port 465. The connection is already encrypted, so `PLAIN`/`LOGIN` here are not cleartext |
| `Unknown` | No `AUTH` in the plaintext EHLO response (often means AUTH is only offered after STARTTLS) |
| `Error: <message>` | Connection failed: host down, port filtered, timeout, or TLS failure |

Note: the script does not send STARTTLS. It only looks at what the server offers before encryption. A server that lists both `STARTTLS` and `AUTH PLAIN LOGIN` in the plaintext response is still reported as `Vulnerable`, because a client can log in without ever starting TLS.

### Example responses

Vulnerable (AUTH offered with no encryption):
```
250-smtp.vulnerable.com Hello test
250-AUTH PLAIN LOGIN
250 HELP
```

Also reported as Vulnerable (STARTTLS available but not enforced):
```
250-smtp.risky.com Hello test
250-STARTTLS
250-AUTH PLAIN LOGIN
250 HELP
```
An attacker in the middle can strip `STARTTLS` from this response and make the client log in in plaintext.

Good configuration (AUTH only offered after STARTTLS, reported as `Unknown`):
```
250-smtp.good.com Hello test
250-STARTTLS
250 HELP
```

---

## Port 465 Notes
Port 465 is SMTP over TLS (SMTPS). This explains some behavior that can look confusing:
- You cannot open `host:465` in a browser. It is a mail port, not a web server.
- Other tools that connect to 465 in plaintext will time out or report false, because the server waits for a TLS handshake before sending anything.
- `AUTH PLAIN LOGIN` on 465 is normal and safe, since the password travels inside TLS.

---

## Manual Verification
Confirm a finding by hand before reporting it. `openssl` is included with Git Bash on Windows.

Plaintext check on 25 or 587 (this is what the finding is about):
```bash
ncat host 587
EHLO test
```
If `AUTH PLAIN` or `AUTH LOGIN` appears here, the finding is confirmed. `telnet host 587` also works.

Check what is offered after STARTTLS:
```bash
openssl s_client -connect host:587 -starttls smtp -crlf -quiet
EHLO test
```

Check port 465:
```bash
openssl s_client -connect host:465 -crlf -quiet
EHLO test
```

---

## Security Risks of Cleartext Login
- Packet sniffing: credentials can be read off the network with tools like Wireshark.
- STARTTLS stripping: if STARTTLS is offered but not required, an attacker can remove it and force a plaintext login.
- Man-in-the-middle: anyone on the network path can capture the credentials.

### How to fix
- Do not offer `AUTH` on unencrypted connections. Offer it only after STARTTLS succeeds, or only on port 465.
- Require STARTTLS for client submission on 587.
- Prefer port 465 (implicit TLS) for client submission where possible.

---

## Example Outputs in Other Formats

### CSV (`results.csv`)
```
host,port,status,banner,cleartext_login_permitted
smtp1.example.com,25,Vulnerable,"250-AUTH PLAIN LOGIN",True
smtp1.example.com,465,Secure (implicit TLS),"250-AUTH PLAIN LOGIN",False
smtp1.example.com,587,Unknown,"250-STARTTLS",False
smtp2.example.com,25,Error: timed out,,False
```

### XLSX (`results.xlsx`)
| Host | Port | Status | Banner | Cleartext Login Permitted |
|---|---|---|---|---|
| smtp1.example.com | 25 | Vulnerable | 250-AUTH PLAIN LOGIN | True |
| smtp1.example.com | 465 | Secure (implicit TLS) | 250-AUTH PLAIN LOGIN | False |
| smtp1.example.com | 587 | Unknown | 250-STARTTLS | False |
| smtp2.example.com | 25 | Error: timed out | | False |

---

## License
This script is open-source and can be modified freely. Use it only on systems you are authorized to test.
