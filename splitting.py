class Budgethack:
    def __init__(self, expenses):
        self.expenses = expenses
        self.members = list(set([x[0] for x in self.expenses]))
        
    def individual_share(self):
        total_spent = float(sum([x[1] for x in self.expenses]))
        return total_spent/len(self.members)

    def individual_balance(self):
        each_share = self.individual_share()
        balances = {}
        for member in self.members:
            expense_of_member = sum([x[1] for x in self.expenses if x[0] == member])
            balances[member] = round(expense_of_member - each_share,2)
        return balances

    def borrowers_and_lenders_balances(self):
        lenders = {}
        borrowers = {}
        member_balances = self.individual_balance()
        for member, balance in member_balances.items():
            if balance > 0:
                lenders[member] = balance
            elif balance < 0:
                borrowers[member] = balance
        return borrowers, lenders

    def pay_borrowed_amount_to_lender(self, borrowed_amt, borrowers, borrower, lenders, lender):
        lenders_amt = round(lenders[lender],2)
        amount_to_pay = lenders_amt if borrowed_amt > lenders_amt else borrowed_amt
        borrowers[borrower] += round(amount_to_pay,2)
        lenders[lender] -= round(amount_to_pay,2)
        borrowed_amt -= round(amount_to_pay,2)
        return [borrower, lender, round(amount_to_pay,2)], borrowed_amt

    def split_expense(self):
        (borrowers, lenders) = self.borrowers_and_lenders_balances()
        transactions = []
        for borrower, borrowed_amt in borrowers.items():
            abs_borrowed_amt = round(abs(borrowed_amt),2)
            #abs_borrowed_amt = abs(borrowed_amt)
            while abs_borrowed_amt > 0.1:
                lender = max(lenders, key=lenders.get)
                transaction, abs_borrowed_amt = self.pay_borrowed_amount_to_lender(abs_borrowed_amt, borrowers, borrower, lenders, lender)
                transactions.append(transaction)
        return transactions