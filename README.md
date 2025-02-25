# SMTP Cleartext Login Permitted Tester

## 🚀 Overview
This script tests whether an SMTP server **allows cleartext authentication (`AUTH PLAIN` or `AUTH LOGIN`)** without encryption, which is a security risk.

- **Single and Bulk Mode**: Test one SMTP server or multiple servers from a file.
- **Progress Bar**: Displays scanning progress for bulk mode.
- **Multiple Output Formats**: JSON (default), CSV, XLSX, TXT.
- **Vulnerability Detection**: Identifies if an SMTP server permits **cleartext login**.
- **Flexible Input Handling**:
  - **Single mode**: Provide a single domain/IP and optionally specify `--port`.
  - **Bulk mode**: Provide a file with `host:port` format for multiple servers.

---

## 🛠 Installation
Ensure you have the required dependencies installed:

```bash
pip install tqdm pandas openpyxl
```
Clone the repository:

```bash
git clone https://github.com/threatlabindonesia/smtp_cleartext_checker.git
cd smtp_cleartext_checker
```

---

## 🔧 Usage

### 1️⃣ **Single Check (Specify Port)**
```bash
python3 smtp_cleartext_checker.py smtp.example.com --port 587
```
- If `--port` is omitted, the default **port 25** is used.

### 2️⃣ **Bulk Check (Multiple Servers, Different Ports)**
Create a file (e.g., `targets.txt`) with the format `host:port`:
```
smtp1.example.com:25
smtp2.example.com:587
smtp3.example.com:465
```
Run:
```bash
python3 smtp_cleartext_checker.py targets.txt --bulk
```
⚠ **Bulk mode requires `host:port` format for each line!**

### 3️⃣ **Saving Results**
You can save results in **CSV, XLSX, TXT, or JSON**:
```bash
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.csv
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.xlsx
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.txt
python3 smtp_cleartext_checker.py targets.txt --bulk --output results.json
```

---

## 📜 Output Format (JSON Example)
By default, results are displayed in JSON format in the CLI:

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

### **📌 Explanation of Output Fields**
| **Field**                    | **Description** |
|------------------------------|--------------------------------------------------------------------|
| `host`                        | The SMTP server being tested. |
| `port`                        | The SMTP port used (e.g., 25, 587, 465). |
| `status`                      | Shows if the server allows **cleartext authentication** or if an error occurred. |
| `banner`                      | The SMTP response after sending `EHLO test`. Lists available authentication methods. |
| `cleartext_login_permitted`   | **`true`** if the server allows **cleartext authentication**, otherwise `false`. |

---

## ❗️ How Vulnerability Detection Works
1. The script **connects to the SMTP server** and sends `EHLO test`.
2. It **parses the SMTP response (banner)**:
   - If it contains **"AUTH PLAIN"** or **"AUTH LOGIN"** → The server supports cleartext authentication.
   - If **"STARTTLS"** is absent → 🚨 **Vulnerable** (passwords sent in plaintext).
   - If it only lists **secure authentication methods** (`CRAM-MD5`, `DIGEST-MD5`) → 🟢 **Secure**.
3. The **status** is determined based on these checks:
   - `"Vulnerable"` → `AUTH PLAIN` or `AUTH LOGIN` **without encryption**.
   - `"Secure"` → No plaintext authentication, or STARTTLS is required.
   - `"Unknown"` → No clear indication from the server.
   - `"Error: <message>"` → Connection issues (server down, blocked, or wrong port).

### **🔎 Example SMTP Banner Responses & Meaning**
#### ✅ **Secure Server (No Cleartext Login)**
```
250-smtp.secure.com Hello test
250-AUTH CRAM-MD5 DIGEST-MD5
250 STARTTLS
250 HELP
```
✔ **Only secure authentication** (`CRAM-MD5`, `DIGEST-MD5`).  
✔ **STARTTLS available**, ensuring encryption before login.

#### 🔴 **Vulnerable Server (Allows Cleartext Login)**
```
250-smtp.vulnerable.com Hello test
250-AUTH PLAIN LOGIN
250 HELP
```
🚨 **Vulnerable**: Supports `PLAIN LOGIN` **without encryption**, meaning credentials can be intercepted.

#### 🟡 **Potentially Secure (Requires STARTTLS)**
```
250-smtp.secureish.com Hello test
250-STARTTLS
250-AUTH PLAIN LOGIN
250 HELP
```
⚠ **Risky**: Supports `AUTH PLAIN` and `LOGIN`, **but requires STARTTLS** for encryption.  
⚠ If a **Man-in-the-Middle (MitM) attacker** blocks STARTTLS, the server remains vulnerable.

---

## ⚠ Security Risks of Cleartext Login
- **Packet Sniffing**: Attackers can intercept plaintext credentials using tools like Wireshark.
- **SMTP Downgrade Attack**: If STARTTLS is available but not enforced, attackers can force clients to authenticate in plaintext.
- **Man-in-the-Middle (MitM) Attacks**: If credentials are sent without encryption, an attacker between the client and server can steal them.

### **🛡 How to Secure SMTP Servers**
✅ **Disable `AUTH PLAIN` and `AUTH LOGIN` on unencrypted connections**.  
✅ **Enforce STARTTLS**: Ensure all authentication happens over a secure connection.  
✅ **Use Strong Authentication**: Prefer **CRAM-MD5, DIGEST-MD5, or OAuth-based authentication**.  
✅ **Block Port 25 for Outbound Mail**: Many ISPs already do this to prevent spam abuse.

---

## 📌 Example Outputs in Other Formats
### **CSV (`results.csv`)**
```
host,port,status,banner,cleartext_login_permitted
smtp1.example.com,25,Vulnerable,"250-AUTH PLAIN LOGIN",True
smtp2.example.com,587,Secure,"250-AUTH CRAM-MD5 DIGEST-MD5",False
smtp3.example.com,465,Error: Connection timeout,,False
```

### **XLSX (`results.xlsx`)**
| **Host**              | **Port** | **Status**      | **Banner**                              | **Cleartext Login Permitted** |
|----------------------|--------|--------------|-------------------------------------|----------------------------|
| smtp1.example.com   | 25     | Vulnerable   | 250-AUTH PLAIN LOGIN               | ✅ (True)                  |
| smtp2.example.com   | 587    | Secure       | 250-AUTH CRAM-MD5 DIGEST-MD5       | ❌ (False)                 |
| smtp3.example.com   | 465    | Error: Timeout | (No banner)                       | ❌ (False)                 |

---

## 📜 License
This script is open-source and can be modified freely. Use it responsibly for security testing and compliance checks.
