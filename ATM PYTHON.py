import time

class ATMSimulation:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance
        self.tras_hist = []
        self.pin = 1234 
    
    def pin_check(self):
        inp_pin = int(input("Enter your PIN: "))
        return inp_pin == self.pin

    def bal_inq(self):
        print("\nChecking balance...")
        time.sleep(1)  
        print(f"Your current balance is: ${self.balance}")
        self.tras_hist.append("Balance inquiry")

    def cash_with(self):
        amt = float(input("\nEnter the amt to withdraw: $"))
        if amt <= 0:
            print("Invalid amount. Please enter a positive value.")
        elif amt > self.balance:
            print("Insufficient funds.")
        else:
            self.balance -= amt
            print(f"Please take your cash: ${amt}")
            self.tras_hist.append(f"Withdraw ${amt}")
        time.sleep(1)

    def cash_dep(self):
        amt = float(input("\nEnter the amount to deposit: $"))
        if amt <= 0:
            print("Invalid amount. Please enter a positive value.")
        else:
            self.balance += amt
            print(f"Deposited: ${amt}")
            self.tras_hist.append(f"Deposited ${amt}")
        time.sleep(1) 

    def change_pin(self):
        old_pin = int(input("\nEnter your current PIN: "))
        if old_pin == self.pin:
            new_pin = int(input("Enter your new PIN: "))
            confirm_pin = int(input("Confirm your new PIN: "))
            if new_pin == confirm_pin:
                self.pin = new_pin
                print("PIN successfully changed.")
                self.tras_hist.append("PIN changed")
            else:
                print("PIN confirmation does not match.")
        else:
            print("Incorrect current PIN.")
        time.sleep(1) 

    def show_tras_hist(self):
        print("\nTransaction History:")
        if not self.tras_hist:
            print("No transactions yet.")
        else:
            for transaction in self.tras_hist:
                print("-", transaction)
        time.sleep(1) 

    def start(self):
        print("Welcome to the ATM Machine")
        
        if not self.pin_check():
            print("Incorrect PIN. Exiting...")
            return

        while True:
            print("\nSelect an option:")
            print("1. Balance Inquiry")
            print("2. Cash Withdrawal")
            print("3. Cash Deposit")
            print("4. Change PIN")
            print("5. Transaction History")
            print("6. Exit")
            
            choice = input("Enter your choice 1-6 : ")
            
            if choice == '1':
                self.bal_inq()
            elif choice == '2':
                self.cash_with()
            elif choice == '3':
                self.cash_dep()
            elif choice == '4':
                self.change_pin()
            elif choice == '5':
                self.show_tras_hist()
            elif choice == '6':
                print("Thank you for using the ATM. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

atm = ATMSimulation(initial_balance=1000) 
atm.start()
