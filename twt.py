import tkinter as tk
from tkinter import messagebox, simpledialog
import pickle
import random
import os
import datetime as dt
import requests


def account_number():
    '''用random set up 一個 login id'''
    return random.randint(1, 99999)

class BalanceException(Exception):
    pass

class TransactionTime: #交易時間 set up
    def __init__(self, amount, transaction_type):
        self.date = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.amount = amount
        self.transaction_type = transaction_type

    def __repr__(self):
        return f"{self.date}: {self.transaction_type} - {self.amount} HKD"

class TermDeposit: #set up 定期
    def __init__(self, amount, term, interest_rate):
        self.amount = amount
        self.term = term
        self.interest_rate = interest_rate
        self.start_date = dt.datetime.now()
        self.end_date = self.start_date + dt.timedelta(days=term * 30)  # 一個月 30日

    def calculate_interest(self):
        return self.amount * (self.interest_rate / 100) * (self.term / 12)

    def __repr__(self):
        interest = self.calculate_interest()
        return f"定期存款: {self.amount} HKD, 期限: {self.term} 個月, 利率: {self.interest_rate}%, 利息: {interest} HKD"

class Account:
    def __init__(self, name='', balance=0, account_id=None):
        self.name = name
        self.balance = balance
        self.account_id = account_id if account_id else account_number()
        self.transactions = []
        self.term_deposits = []

    def add_transaction(self, amount, transaction_type):
        transaction = TransactionTime(amount, transaction_type)
        self.transactions.append(transaction)

    def deposit(self, amount):#存款
        self.balance += amount
        self.add_transaction(amount, "存款")
        print("\n存款成功.")
        self.get_balance()
        self.save_file()

    def viable_transaction(self, amount):#設定一個如果錢不足的結果
        if self.balance >= amount:
            return
        else:
            raise BalanceException(
                f"sorrt，户口'{self.account_id}'\n{self.name} 只有 HKD 结餘$:{self.balance}"
            )

    def withdraw(self, amount): # 提款
        try:
            self.viable_transaction(amount)
            self.balance -= amount
            self.add_transaction(amount, "提款")
            print("\n提款成功")
            self.get_balance()
            self.save_file()
        except BalanceException as e:
            print(f"\n提款不成功: {e}")

    def transfer(self, amount, account): # 用戶轉賬
        try:
            print('\n**********\n\n開始用戶轉賬中..😊')
            self.viable_transaction(amount)
            self.balance -= amount
            account.balance += amount
            self.add_transaction(amount, "將轉賬到 " + str(account.account_id))
            account.add_transaction(amount, "從 " + str(self.account_id) + " 收到轉賬")
            print("\n轉賬成功✅!!!")
            self.get_balance()
            self.save_file()
            account.save_file()
        except BalanceException as e:
            print(f"\n轉賬不成功: {e}")

    def create_term_deposit(self, amount, term, interest_rate): #set up 定期規則
        try:
            if amount < 10000:
                raise BalanceException("定期存款金額至少為 HKD 10000.")
            if term not in [3, 6, 12]:
                raise BalanceException("定期存款期限必須為 3, 6 或 12 個月.")
            self.viable_transaction(amount)
            self.balance -= amount
            term_deposit = TermDeposit(amount, term, interest_rate)
            self.term_deposits.append(term_deposit)
            self.add_transaction(amount, "定期存款")
            print("\n定期存款成功")
            self.get_balance()
            self.save_file()
        except BalanceException as e:
            print(f"\n定期存款不成功: {e}")

    def change_name(self):
        new_name = input("请输入新姓名: ")
        self.name = new_name
        print(f"姓名已成功更改為: {self.name}")
        self.save_file()

    def get_balance(self):
        print(f"\n賬户'{self.account_id}'\n{self.name} 结餘為 HKD$:{self.balance}\n")

    def show_transactions(self):
        print(f"\n賬户'{self.account_id}'\n{self.name} 的交易记录:")
        for transaction in self.transactions:
            print(transaction)
        print("\n")

    def show_term_deposits(self):
        print(f"\n賬户'{self.account_id}'\n{self.name} 的定期存款:")
        for deposit in self.term_deposits:
            print(deposit)
        print("\n")

    def save_file(self):
        with open(f"{self.account_id}.pkl", "wb") as file:
            pickle.dump(self, file)
        print("\n賬户信息已保存.")

    @staticmethod
    def load_file(account_id):
        if os.path.exists(f"{account_id}.pkl"):
            with open(f"{account_id}.pkl", "rb") as file:
                account = pickle.load(file)
            return account
        else:
            print(f"\n未找到賬户'{account_id}'的資料請確定.")
            return None
            
class ForexAccount(Account):
    def __init__(self, name='', balance=0, account_id=None):
        super().__init__(name, balance, account_id)
        self.type = 'F'
        self.portfolio_dict = {'HKD': 0, 'USD': 0, 'RMB': 0}

    def show_currencies(self):
        print("\n當前外匯投資組合:")
        for currency, amount in self.portfolio_dict.items():
            print(f"{currency}: {amount}")

    def portfolio_summary(self):
        total_balance_hkd = 0
        for currency, amount in self.portfolio_dict.items():
            rate = self.get_exchange_rate(currency, 'HKD')
            total_balance_hkd += amount * rate
        print(f"\n投資組合總值 (以 HKD 計算): {total_balance_hkd:.2f} HKD")
        self.save_file()

    def deposit(self, amount, currency='HKD'):
        if currency not in self.portfolio_dict:
            print(f"\n不支持的貨幣: {currency}")
        else:
            self.portfolio_dict[currency] += amount
            print(f"\n已成功存入 {amount} {currency}")
            self.save_file()

    def withdraw(self, amount, currency='HKD'):
        if currency not in self.portfolio_dict:
            print(f"\n不支持的貨幣: {currency}")
        elif self.portfolio_dict[currency] < amount:
            print(f"\n餘額不足，無法取出 {amount} {currency}")
        else:
            self.portfolio_dict[currency] -= amount
            print(f"\n已成功取出 {amount} {currency}")
            self.save_file()

    def convert_currency(self, amount, from_currency, to_currency):
        if from_currency not in self.portfolio_dict or to_currency not in self.portfolio_dict:
            print(f"\n不支持的貨幣: {from_currency} 或 {to_currency}")
            return

        from_rate = self.get_exchange_rate(from_currency, 'HKD')
        to_rate = self.get_exchange_rate(to_currency, 'HKD')

        if from_rate == 0 or to_rate == 0:
            print("\n無法獲取匯率，請稍後再試。")
            return

        converted_amount = amount * from_rate / to_rate

        if self.portfolio_dict[from_currency] < amount:
            print(f"\n{from_currency} :餘額不足，無法轉換: {amount} {from_currency}")
        else:
            self.portfolio_dict[from_currency] -= amount
            self.portfolio_dict[to_currency] += converted_amount
            print(f"\n已成功将 {amount} {from_currency} 轉換為 {converted_amount:.2f} {to_currency}")

    def balance(self):
        self.show_currencies()
        self.portfolio_summary()

    def get_exchange_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return 1.0
        api_url = 'https://cdn.moneyconvert.net/api/latest.json'
        try:
            response = requests.get(api_url)
            rates = response.json().get('rates')
            if rates:
                from_rate = rates.get(from_currency, 1.0)
                to_rate = rates.get(to_currency, 1.0)
                return to_rate / from_rate
        except Exception as e:
            print(f"\n無法獲取匯率: {e}")
        return 0.0

def create_account():
    name = input("请输入您的姓名: ")
    account_type = input("請選擇賬戶類型（N：普通賬戶，F：外匯賬戶）: ")
    
    if account_type.upper() == 'F':
        account = ForexAccount(name=name)
        print("您已選擇創建外匯賬戶。")
    else:
        account = Account(name=name)
        print("您已選擇創建普通賬戶。")

    account.save_file()
    print(f"\n賬戶已成功創建，賬戶號碼為: {account.account_id}。這是登錄號碼，請妥善保存。")
# bank acc
class BankAccount:
    def __init__(self, name, balance=0):
        self.name = name
        self.balance = balance
        self.term_deposits = []

    def deposit(self, amount):
        self.balance += amount
        return f"存款 ${amount:.2f} 成功。當前餘額: ${self.balance:.2f}"

    def withdraw(self, amount):
        if amount > self.balance:
            return "餘額不足"
        self.balance -= amount
        return f"取款 ${amount:.2f} 成功。當前餘額: ${self.balance:.2f}"

    def create_term_deposit(self, amount, duration):
        if amount > self.balance:
            return "餘額不足以創建定期存款"
        self.balance -= amount
        self.term_deposits.append({"amount": amount, "duration": duration})
        return f"成功創建 ${amount:.2f} 的 {duration} 個月定期存款"

    def change_name(self, new_name):
        old_name = self.name
        self.name = new_name
        return f"姓名已從 {old_name} 更改為 {new_name}"
    
    def save_file(self):
        with open(f"{self.name}.pkl", "wb") as file:
            pickle.dump(self, file)
        print("\n賬户信息已保存.")

    @staticmethod
    def load_file(name):
        if os.path.exists(f"{name}.pkl"):
            with open(f"{name}.pkl", "rb") as file:
                account = pickle.load(file)
            return account
        else:
            print(f"\n未找到賬户'{name}'的資料請確定.")
            return None


class BankGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Ryan Bank")
        self.master.geometry("400x300")
        self.current_account = None

        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_main_menu()

    def create_main_menu(self):
        tk.Button(self.main_frame, text="創建新賬戶", command=self.create_account).pack(pady=10)
        tk.Button(self.main_frame, text="登入賬戶", command=self.login).pack(pady=10)
        tk.Button(self.main_frame, text="退出", command=self.master.quit).pack(pady=10)

    def create_account(self):
        name = simpledialog.askstring("創建賬戶", "請輸入您的姓名:")
        if name:
            account_type = simpledialog.askstring("創建賬戶", "請選擇賬戶類型（N：普通賬戶，F：外匯賬戶）:")
            if account_type.upper() == 'F':
                account = ForexAccount(name=name)
                messagebox.showinfo("賬戶創建", "您已選擇創建外匯賬戶。")
            else:
                account = BankAccount(name=name)
                messagebox.showinfo("賬戶創建", "您已選擇創建普通賬戶。")
            account.save_file()
            messagebox.showinfo("賬戶創建", f"賬戶已成功創建，賬戶號碼為: {account.account_id}")

    def login(self):
        account_id = simpledialog.askinteger("登入", "請輸入您的賬戶號碼:")
        if account_id:
            account = BankAccount.load_file(account_id)
            if account:
                self.current_account = account
                self.show_account_menu()
            else:
                messagebox.showerror("錯誤", "賬戶不存在!")

    def show_account_menu(self):
        self.clear_frame()
        tk.Button(self.main_frame, text="存款", command=self.deposit).pack(pady=5)
        tk.Button(self.main_frame, text="取款", command=self.withdraw).pack(pady=5)
        tk.Button(self.main_frame, text="定期存款", command=self.create_term_deposit).pack(pady=5)
        tk.Button(self.main_frame, text="更改姓名", command=self.change_name).pack(pady=5)
        tk.Button(self.main_frame, text="查詢結餘", command=self.show_balance).pack(pady=5)
        tk.Button(self.main_frame, text="顯示定期存款", command=self.show_term_deposits).pack(pady=5)
        if isinstance(self.current_account, ForexAccount):
            tk.Button(self.main_frame, text="外匯功能", command=self.forex_menu).pack(pady=5)
        tk.Button(self.main_frame, text="登出", command=self.logout).pack(pady=5)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def deposit(self):
        amount = simpledialog.askfloat("存款", "請輸入存款金額:")
        if amount:
            result = self.current_account.deposit(amount)
            messagebox.showinfo("存款", result)

    def withdraw(self):
        amount = simpledialog.askfloat("取款", "請輸入取款金額:")
        if amount:
            result = self.current_account.withdraw(amount)
            messagebox.showinfo("取款", result)

    def create_term_deposit(self):
        amount = simpledialog.askfloat("定期存款", "請輸入定期存款金額:")
        duration = simpledialog.askinteger("定期存款", "請輸入定期存款期限（月）:")
        if amount and duration:
            result = self.current_account.create_term_deposit(amount, duration)
            messagebox.showinfo("定期存款", result)

    def change_name(self):
        new_name = simpledialog.askstring("更改姓名", "請輸入新的姓名:")
        if new_name:
            result = self.current_account.change_name(new_name)
            messagebox.showinfo("更改姓名", result)

    def show_balance(self):
        balance = self.current_account.balance
        messagebox.showinfo("結餘", f"當前結餘為: ${balance:.2f}")

    def show_term_deposits(self):
        if not self.current_account.term_deposits:
            messagebox.showinfo("定期存款", "目前沒有定期存款")
        else:
            deposits = "\n".join([f"${d['amount']:.2f} 為期 {d['duration']} 個月" for d in self.current_account.term_deposits])
            messagebox.showinfo("定期存款", deposits)

    def logout(self):
        self.current_account = None
        self.create_main_menu()

    def forex_menu(self):
        self.clear_frame()
        tk.Button(self.main_frame, text="查看貨幣持倉", command=self.show_currencies).pack(pady=5)
        tk.Button(self.main_frame, text="存入貨幣", command=self.deposit_currency).pack(pady=5)
        tk.Button(self.main_frame, text="取出貨幣", command=self.withdraw_currency).pack(pady=5)
        tk.Button(self.main_frame, text="查看投資組合總值", command=self.show_portfolio_summary).pack(pady=5)
        tk.Button(self.main_frame, text="返回", command=self.show_account_menu).pack(pady=5)

    def show_currencies(self):
        currencies = "\n".join(f"{currency}: {amount}" for currency, amount in self.current_account.portfolio_dict.items())
        messagebox.showinfo("貨幣持倉", currencies)

    def deposit_currency(self):
        currency = simpledialog.askstring("存入貨幣", "請輸入貨幣類型 (如 USD, RMB):")
        if currency:
            amount = simpledialog.askfloat("存入貨幣", f"請輸入存入{currency}金額:")
            if amount:
                result = self.current_account.deposit(amount, currency)
                messagebox.showinfo("存入貨幣", result)

    def withdraw_currency(self):
        currency = simpledialog.askstring("取出貨幣", "請輸入貨幣類型 (如 USD, RMB):")
        if currency:
            amount = simpledialog.askfloat("取出貨幣", f"請輸入取出{currency}金額:")
            if amount:
                result = self.current_account.withdraw(amount, currency)
                messagebox.showinfo("取出貨幣", result)

    def show_portfolio_summary(self):
        summary = self.current_account.portfolio_summary()
        messagebox.showinfo("投資組合總值", summary)

if __name__ == "__main__":
    root = tk.Tk()
    app = BankGUI(root)
    root.mainloop()