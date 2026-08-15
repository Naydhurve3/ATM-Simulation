# 13. Inter-bank Relationships — How Banks Interact

> **Research domain doc** · V1 Banking Core · Who owes whom, who settles, and how money actually
> moves between banks — through RBI, NPCI, CCIL, correspondent banks, and the money market.

---

## 1. The ecosystem map

```mermaid
flowchart TD
    RBI["RBI<br/>(central bank — lender of last resort,<br/>settlement bank, regulator)"]
    NPCI["NPCI<br/>(retail rails: UPI/IMPS/NACH/CTS/RuPay)"]
    CCIL["CCIL<br/>(G-sec & forex clearing/settlement)"]
    SWIFT["SWIFT<br/>(cross-border messaging)"]

    A["Bank A"] -->|"current account + CRR at RBI"| RBI
    B["Bank B"] -->|"current account + CRR at RBI"| RBI
    A -->|"UPI/IMPS/NACH settlement"| NPCI
    B -->|"UPI/IMPS/NACH settlement"| NPCI
    A -->|"G-sec deals / forex"| CCIL
    B -->|"G-sec deals / forex"| CCIL
    A <-->|"correspondent/ostro<br/>nostro & vostro"| SWIFT
    B <-->|"correspondent banking"| SWIFT
    A <-->|"inter-bank money market<br/>(call, repo, CBLO)"| B
```

---

## 2. The settlement layer: every bank has an account at RBI

The **current account each bank holds at RBI** is the ultimate settlement ledger. When Bank A
must pay Bank B (any rail), the final step is always an entry between these two RBI accounts.

```mermaid
flowchart LR
    subgraph RBI_LEDGER["RBI — Bank A and Bank B current accounts"]
        CA["Bank A's account"] <-->|"debit/credit"| CB["Bank B's account"]
    end
    X["NEFT / RTGS / clearing result"] --> CA
    CA --> CB
    CB --> Y["Done — funds are final & irrevocable"]
```

- **CRR** is held within this same RBI relationship (3% of NDTL since Nov 2025).
- **SLR** (18%) is a separate portfolio of G-secs the bank owns (liquidity buffer).
- If a bank is short at end of day → it borrows: repo from RBI (5.25%) or from other banks.

---

## 3. Correspondent banking — nostro & vostro

For **cross-border** payments, banks rarely have direct accounts in every country. They use
**correspondent banks**:

| Account | Whose perspective | Meaning |
|---|---|---|
| **Nostro** ("ours") | Bank A's view | "Our account held at Bank B (abroad)" |
| **Vostro** ("yours") | Bank B's view | "Your account held at us" |
| **Loro** ("theirs") | Third bank's view | Account held by a third party for another |

```mermaid
sequenceDiagram
    participant X as Indian Bank (payer)
    participant C as Correspondent (e.g., US bank)
    participant Y as Foreign Bank (payee)

    X->>C: SWIFT MT103 (payment instruction)
    C->>C: Debit X's nostro (if prefunded) or extend credit
    C->>Y: SWIFT MT103 (credit Y)
    Y->>Y: Credit customer account
    Note over X,Y: Final settlement may go through Fedwire/CHIPS —<br/>SWIFT is the messaging, not the money movement
```

India's **Rupee Vostro mechanism** (2022–23, after RBI's internationalisation push) lets partner
country banks hold vostro accounts in India and settle trade in INR directly — bypassing USD
correspondent chains.

---

## 4. Retail rails settlement — NPCI

- NPCI runs a **settlement account** structure: banks pre-fund the account; net obligations are
  settled multiple times daily.
- RuPay (card network) also settles through NPCI.
- UPI settlement happens near-continuously (multiple batches) → low counterparty risk.

---

## 5. The inter-bank money market

Banks manage daily liquidity with each other (and with RBI):

| Instrument | What it is | Current anchor |
|---|---|---|
| **Call money** | Unsecured overnight borrowing between banks | Market-driven |
| **Repo (Liquidity Adjustment Facility)** | Banks borrow from RBI against G-secs | **5.25%** |
| **SDF** | Banks park surplus cash with RBI | **5.00%** |
| **MSF** | Emergency borrowing from RBI (up to SLR %) | **5.50%** |
| **CBLO** | Collateralised borrowing-lending on CCIL platform | Market-driven |
| **Inter-bank FD/placements** | Term deposits between banks | Market-driven |

```mermaid
flowchart LR
    B1["Bank short of cash"] -->|"repo @5.25% or call money"| RBI["RBI / other banks"]
    B2["Bank with surplus cash"] -->|"SDF @5.00% or call money"| RBI
```

The repo rate therefore becomes the **floor cost of money** for every bank — which is why loan
rates (MCLR/EBLR) track it (see doc 16).

---

## 6. What this means for the simulation

The repo's simulator is **single-bank** (`ATMService` handles one account ledger), but it models
the concepts:

- `banking_core.bank_attributes.get_bank_attrs()` — bank-specific fee/limit structures
  (e.g., other-bank ATM fees) = the interchange/institution layer.
- `target_bank` fields in transactions = the *other* bank in a transfer.
- `bank_clustering` / `market_share` analytics = how banks compare in the ecosystem (real RBI CSV).

**Next doc:** [`14-loans-and-credit.md`](14-loans-and-credit.md) — loan types, eligibility and RBI norms.
