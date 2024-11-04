# ATM Simulation Program in Python
This is an ATM simulation program developed in Python, created as part of my Python Development internship at OctaNet. The program simulates key functionalities of an ATM, including balance inquiry, cash withdrawal, cash deposit, PIN change, and transaction history. It also ensures secure access with a PIN verification system.

-Table of Contents
-Overview
-Features
-Getting Started
-Class Structure and Method Descriptions
-Usage
-License

## Overview
The ATMSimulation program allows users to interact with a virtual ATM machine through a console-based interface. Users are prompted to enter their PIN to gain access and are then able to perform various banking transactions, such as checking their balance, depositing and withdrawing cash, changing their PIN, and viewing transaction history.

##Features
-`PIN Verification`: Ensures secure access by requiring the correct PIN before performing any transactions.
-`Balance Inquiry`: Displays the user's current account balance.
-`Cash Withdrawal`: Allows users to withdraw cash, ensuring sufficient balance and positive withdrawal amounts.
-`Cash Deposit`: Allows users to deposit cash, with validation for positive deposit amounts.
-`PIN Change`: Users can change their PIN after verifying their current PIN.
-`Transaction History`: Records and displays a history of user transactions.
-`Error Handling`: Provides validation for invalid inputs, such as insufficient balance or incorrect PIN.
## Getting Started
### Prerequisites
- Python 3.x is required to run this program.
Installation
Clone this repository to your local machine:
Copy code
```
git clone https://github.com/YourGitHubUsername/ATMSimulation.git
```
- Navigate to the project directory:
Copy code
```
cd ATMSimulation
```
- Run the program:
Copy code
```
python atm_simulation.py
```
## Class Structure and Method Descriptions
### class ATMSimulation
- Attributes
-`balance`: Stores the current account balance. Initialized with a default balance (e.g., $1000).
-`tras_hist`: Keeps a record of transaction history.
-`pin`: The default PIN set for secure access (default is 1234).
- Methods
`__init__(self, initial_balance=0)`: Initializes the ATM with an optional starting balance and sets up an empty transaction history and a default PIN.

`pin_check(self)`: Prompts the user to input their PIN and checks if it matches the stored PIN. Returns True if the input PIN is correct; otherwise, False.

`bal_inq(self)`: Displays the current balance to the user and logs this action in the transaction history as "Balance inquiry."

`cash_with(self)`: Allows the user to withdraw a specified amount. Validates if the entered amount is positive and if there are sufficient funds. Updates the balance and logs the transaction if successful.

`cash_dep(self)`: Allows the user to deposit a specified amount. Ensures the amount is positive, updates the balance, and records the deposit in the transaction history.

`change_pin(self)`: Allows the user to change their PIN by verifying the current PIN and confirming the new PIN. Updates the PIN if both entries match and logs the PIN change.

`show_tras_hist(self)`: Displays the transaction history. If there are no transactions, it informs the user accordingly.

`start(self)`: The main method to run the ATM simulation. It verifies the PIN and then presents a menu of options, allowing the user to choose among the features listed above. The loop continues until the user selects the "Exit" option.

## Usage
Upon running the program, users will see the following menu options:

- `Balance Inquiry` - Check current balance.
- `Cash Withdrawal` - Withdraw a specified amount from the balance.
- `Cash Deposit` - Deposit a specified amount to the balance.
- `Change PIN` - Update the account PIN securely.
- `Transaction History` - Review a list of previous transactions.
- `Exit` - Terminate the session.
### Example
Run the program.
Enter the default PIN (1234).
Select a transaction option (e.g., "1" for Balance Inquiry).
Follow on-screen instructions for each option.
License
This project is licensed under the MIT License. Feel free to fork, clone, or use this code for personal projects.

This README provides an overview of the ATM Simulation project, its features, and instructions on how to get started with the code. For a detailed code walkthrough, refer to the atm_simulation.py file or check out the video explanation linked in the project repository.
