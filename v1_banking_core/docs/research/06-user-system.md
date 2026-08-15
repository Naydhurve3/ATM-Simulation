# User System Architecture

## Registration Flow

```
                     UserManager.login_or_register()
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
              [L] Login                [R] Register
                    |                       |
                    v                       v
            Enter user_id/pin       Enter: name, age, phone,
                    |                 email, bank, income_bracket
                    |                       |
                    v                       v
            Verify credentials        validate_name(), validate_phone(),
                    |                  validate_email(), validate_age()
                    |                       |
                    |             +---------+---------+
                    |             |                   |
                    v        [Adult >= 18]       [Minor < 18]
                    |             |                   |
                    |             v                   v
                    |       Set is_minor=False  Require guardian:
                    |                           name, phone, relation
                    |             |                   |
                    |             +---------+---------+
                    |                       |
                    v                       v
            Return user dict      Generate:
                                   - account_no (ACCT-XXXXXXXXXX)
                                   - card_no (XXXX-XXXX-XXXX-XXXX)
                                   - PIN (4-digit, hashed)
                                   - credit_score (rule-based)
                                   - Generate initial passbook
                                   - Insert into ecosystem.db
                                   
                                   
                       Forgot Card / PIN / Recovery
                                |
                    +-----------+-----------+
                    |                       |
            [F] Forgot Card No      [P] Forgot PIN
                    |                       |
                    v                       v
            Enter phone + email     Enter user_id + recovery_code
                    |                       |
                    v                       v
            Verify identity         Verify recovery code
                    |                       |
                    v                       v
            Display card number     Reset PIN (new 4-digit)
```

## Account Generation

### Account Number
- Format: `ACCT-XXXXXXXXXX` (10 random digits)
- Unique constraint in database

### Card Number
- Format: `XXXX-XXXX-XXXX-XXXX` (16 digits)
- Generated via Luhn algorithm for checksum validity

### PIN
- 4-digit numeric
- Stored as reversible hash (simple mapping for demo purposes)
- Changeable via ATM menu

### Credit Score (New User)
- Adult (18-25): 650
- Adult (26-40): 700
- Adult (41-60): 750
- Adult (60+): 780
- Minor: 400 (capped at 600 max)
- Adjusted by income bracket

## KYC Levels

| Level | Requirements | Features |
|-------|-------------|----------|
| Basic | Name, Age, Phone | Register, Login, View balance |
| Standard | + Email | Transactions up to 50,000/day |
| Full KYC | + Guardian (minors) | All features including loans |

## Session Management

```
UserManager.end_session(user_id)
  +--> Update atm_last_used
  +--> Log session to atm_sessions
  +--> Clean up any temporary state

UserManager.get_user(user_id)
  +--> Refresh user data from database
  +--> Returns updated dict (balance, credit_score, etc.)
```

## Daily Usage Tracking

```
ATMSimulator._check_daily_limit(amount)
  +--> Reads user.atm_daily_usage
  +--> Reads user.atm_last_used
  +--> If last_used is not today: reset usage to 0
  +--> If usage + amount > 50000: reject with message
  +--> Else: approve, update usage counter
```

## Multi-Account Detection

```
ReportGenerator._find_linked_accounts(user)
  +--> Query users table for:
  |      * Same name (LOWER match)
  |      * Same phone
  |      * Same email
  +--> Return list of all matching user_ids
  +--> Used by Passbook to aggregate all accounts
```

## Passbook System

### Generation Flow

```
User requests passbook (Profile menu → Option 10)
  |
  +--> ReportGenerator.generate_passbook(user, txns)
  |      |
  |      +--> _find_linked_accounts(user)  # multi-account support
  |      +--> Format selection:
  |      |      * PNG if <= 20 total transactions (PyMuPDF render)
  |      |      * PDF if > 20 transactions (fpdf2)
  |      +--> Content:
  |      |      * User name, account summary
  |      |      * Per-account sections
  |      |      * All transactions (date, type, amount, balance)
  |      |      * Summary statistics
  |      |      * ML insights (credit score, churn risk, cluster)
  |      |      * Charts (spending trend, category pie)
  |      +--> Filename: passbook_[user_id]_[name_slug].png/.pdf
  |      +--> Overwrites previous version
  |      +--> Prompts user to open file
  |
  +--> Also can generate:
         * Account Summary Card (PDF)
         * Account Data Export (JSON)
```

### File Naming Convention

| Asset | Format | Example |
|-------|--------|---------|
| Passbook | `passbook_[id]_[slug].[ext]` | `passbook_1_john_doe.png` |
| Summary Card | `summary_[id]_[slug].pdf` | `summary_1_john_doe.pdf` |
| JSON Export | `account_data_[id]_[slug].json` | `account_data_1_john_doe.json` |

All files are stored in `outputs/reports/` and overwritten on each generation (single file per user).

## Transaction Types

| Type | Description | Balance Effect |
|------|-------------|----------------|
| withdraw | Cash withdrawal | Decrease |
| deposit | Cash/check deposit | Increase |
| transfer | Fund transfer to another account | Decrease |
| fee | ATM/transaction fee | Decrease |
| credit | Interest/refund | Increase |
| payment | Bill payment | Decrease |

Each transaction stores `balance_before` and `balance_after` for audit trail.
