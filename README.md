## Orlanda Engineering – Feedback Email Sender

This project sends personalized HTML feedback request emails to clients pulled from a monday.com board, using a Gmail account via the Gmail API.  
Each successful send is logged to `sent_log.csv` so you can track which clients were contacted.

### Features

- **monday.com integration**: Fetches client records (email, client ID, company, etc.) from a configured board.
- **HTML email template**: Uses `email-he.html` for a branded, RTL Hebrew feedback request email.
- **Gmail API**: Sends emails via a Gmail account using OAuth credentials.
- **Per‑send logging**: Appends a row to `sent_log.csv` for each successfully sent email.
- **Safe testing**: Supports dry‑run mode and test recipient redirection.

### Project structure

- **`main.py`**: CLI entry point. Loads configuration, fetches clients from monday.com, builds the email, and sends/logs messages.
- **`monday_client.py`**: Contains types and helpers to query monday.com (uses `MONDAY_*` variables from `.env`).
- **`email_template.py`**: Builds the email subject and HTML/text body, based on `email-he.html`.
- **`gmail_client.py`**: Wraps Gmail API calls for sending HTML emails.
- **`config.py`**: Loads configuration from environment variables (`.env`) into `AppConfig`.
- **`email-he.html`**: The HTML email template (Hebrew, RTL).
- **`.env`** (not committed): Local environment configuration (tokens, IDs, email settings).
- **`sent_log.csv`** (not committed): Log of all successfully sent emails.

### Requirements

- **Python**: 3.10+ recommended.
- **A monday.com API token** with access to the relevant board.
- **A monday.com board** with at least:
  - A primary email column (`MONDAY_EMAIL_COLUMN_ID`)
  - A client ID column (`MONDAY_CLIENT_ID_COLUMN_ID`)
  - A feedback link column (`MONDAY_FEEDBACK_LINK_COLUMN_ID`)
- **A Gmail account & OAuth credentials** (JSON file downloaded from Google Cloud Console).

Python dependencies are listed in `requirements.txt`:

- `requests`
- `python-dotenv`
- `google-api-python-client`
- `google-auth-httplib2`
- `google-auth-oauthlib`

### Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>.git
   cd "send emails"
   ```

2. **Create and activate a virtual environment (recommended)**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows PowerShell / CMD
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file**

   In the project root (`send emails`), create a file named `.env` and define the required variables (do **not** commit real tokens or secrets):

   ```env
   # monday.com
   MONDAY_API_TOKEN=your_monday_api_token
   MONDAY_BOARD_ID=your_board_id

   MONDAY_EMAIL_COLUMN_ID=your_email_column_id
   MONDAY_CLIENT_ID_COLUMN_ID=your_client_id_column_id
   MONDAY_FEEDBACK_LINK_COLUMN_ID=your_feedback_link_column_id

   # Optional columns
   MONDAY_FIRST_NAME_COLUMN_ID=first_name
   MONDAY_COMPANY_COLUMN_ID=company

   # Gmail
   GMAIL_SENDER_EMAIL=your_sender_email@yourdomain.com
   GMAIL_CREDENTIALS_FILE=credentials.json

   # Optional overrides
   # GMAIL_TOKEN_FILE=token.json
   # EMAIL_SUBJECT_TEMPLATE=We'd love your feedback, {first_name}
   # DRY_RUN=true
   # TEST_RECIPIENT=you@example.com
   ```

5. **Add Gmail `credentials.json`**

   - In Google Cloud Console, create OAuth client credentials for the Gmail API.
   - Download the JSON file and save it as `credentials.json` in the project root (`send emails`).
   - The first run will perform an OAuth flow and create a token file (e.g. `token.json`); both files are ignored by `.gitignore`.

### Usage

From the project directory:

```bash
python main.py [--dry-run] [--client-id <CLIENT_ID>] [--test-recipient <EMAIL>]
```

- **`--dry-run`**: Fetch records and build emails, but **do not** actually send.
- **`--client-id`**: Limit sending to a single client ID from the monday.com board.
- **`--test-recipient`**: Send all emails to this address instead of each client’s real email.

Examples:

- **Dry run for all clients**

  ```bash
  python main.py --dry-run
  ```

- **Send real emails to a single client**

  ```bash
  python main.py --client-id 12345
  ```

- **Send to a test inbox only**

  ```bash
  python main.py --test-recipient you@example.com
  ```

### Logging

- Every successfully sent email is appended to `sent_log.csv` with:
  - UTC timestamp
  - monday.com board ID
  - client ID
  - original email cell value
  - actual recipient email
  - company name (if available)

This file is ignored by Git so real client data is not pushed to GitHub.

### Security & GitHub hygiene

- **Never commit** `.env`, `credentials.json`, `token.json`, or any other files that contain secrets or real client data.
- `/.venv/`, `.env`, credentials and token files, and `sent_log.csv` are all covered in `.gitignore` in this project.

### monday.com → Gmail feedback sender

This small Python script reads client data from a monday.com board and sends personalized HTML feedback-request emails via your corporate Gmail account.

#### 1. Install dependencies

From the `send emails` folder, run:

```bash
pip install -r requirements.txt
```

#### 2. Configure environment variables

Create a `.env` file in the same folder as `main.py` with at least:

```bash
MONDAY_API_TOKEN=your_monday_personal_api_token
MONDAY_BOARD_ID=123456789

MONDAY_EMAIL_COLUMN_ID=email
MONDAY_CLIENT_ID_COLUMN_ID=client_id
MONDAY_FEEDBACK_LINK_COLUMN_ID=feedback_link
# Optional personalization columns:
MONDAY_FIRST_NAME_COLUMN_ID=first_name
MONDAY_COMPANY_COLUMN_ID=company

GMAIL_SENDER_EMAIL=you@yourcompany.com
GMAIL_CREDENTIALS_FILE=credentials.json
# Optional overrides:
# GMAIL_TOKEN_FILE=token.json
# EMAIL_SUBJECT_TEMPLATE=We'd love your feedback, {first_name}
# DRY_RUN=true
# TEST_RECIPIENT=your_test_email@yourcompany.com
```

- Column IDs should match the column IDs from your monday.com board.
- Keep your `.env` file and `credentials.json` out of git / backups that you share.

#### 3. Set up Gmail API

1. Go to the Google Cloud Console and create a project (or reuse an existing one).
2. Enable the **Gmail API** for that project.
3. Create **OAuth client ID** credentials of type “Desktop app”.
4. Download the `credentials.json` file into this folder.

The first time you run the script (without `DRY_RUN=true`), a browser window will open asking you to grant your account permission to send email. After you approve, a `token.json` file will be created and reused on subsequent runs.

#### 4. Run the script

Basic dry-run (no emails actually sent, but everything else runs):

```bash
python main.py --dry-run
```

Actually send emails to the real client email addresses from monday.com:

```bash
python main.py
```

Send all emails to a single test email address (so you can verify formatting):

```bash
python main.py --test-recipient you@yourcompany.com
```

Send only to a single client (matching the client ID column in monday.com):

```bash
python main.py --client-id SOME_CLIENT_ID
```

#### 5. How it works

- `main.py` loads configuration, fetches all items from your specified monday.com board, and iterates over them.
- `monday_client.py` calls the monday.com GraphQL API and converts board items into `ClientRecord` objects.
- `email_template.py` builds a personalized HTML email (and plain-text fallback) using the client’s name, company, and feedback link.
- `gmail_client.py` sends the email via the Gmail API as your configured sender.
- `config.py` reads environment variables (and `.env`) and bundles them into a typed `AppConfig` object.

Use `--dry-run` and/or `TEST_RECIPIENT` to safely test before sending to real clients.

