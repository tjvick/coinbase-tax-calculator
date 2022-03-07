import pandas as pd
from dataclasses import dataclass
from datetime import datetime

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


@dataclass
class Order:
    order_id: str
    date: str
    usd_amount: float
    order_type: str
    currency: str
    currency_quantity: float


def order_from_group_of_transaction_records(name, group):
    usd_amount = group[group['amount/balance unit'] == 'USD'].amount.sum()
    return Order(
        order_id=name,
        date=group.time.min(),
        usd_amount=usd_amount,
        order_type='buy' if usd_amount < 0 else 'sell',
        currency=group[group['amount/balance unit'] != 'USD']['amount/balance unit'].min(),
        currency_quantity=group[group['amount/balance unit'] != 'USD'].amount.sum()
    )


@dataclass
class Position:
    currency: str
    purchase_date: datetime
    currency_quantity: float
    cost_basis: float
    sell_date: datetime = None
    proceeds: float = 0
    closed: bool = False


class Positions:
    def __init__(self):
        self.df = pd.DataFrame(columns=Position.__annotations__.keys())

    def add(self, new_position):
        self.df = pd.concat([self.df, pd.DataFrame([new_position])], ignore_index=True)

    def create_open_position(self, order):
        new_position = Position(
            currency=order.currency,
            purchase_date=order.date,
            cost_basis=-order.usd_amount,
            currency_quantity=order.currency_quantity
        )
        self.add(new_position)

    def get_open_positions(self):
        return self.df[(self.df['currency'] == order.currency) & (self.df['closed'] == False)].sort_values(
            by="purchase_date")

    @property
    def total_cost_basis(self):
        return self.df[self.df['closed'] == True]['cost_basis'].sum()

    @property
    def total_proceeds(self):
        return self.df[self.df['closed'] == True]['proceeds'].sum()

    def close_position_equal_to_sale(self, position_ix, order):
        self.df.loc[position_ix]['closed'] = True
        self.df.loc[position_ix]['sell_date'] = order.date
        self.df.loc[position_ix]['proceeds'] = order.usd_amount

    def close_position_as_fraction_of_sale(self, position_ix, order, open_position):
        self.df.loc[position_ix]['closed'] = True
        self.df.loc[position_ix]['sell_date'] = order.date
        self.df.loc[position_ix]['proceeds'] = order.usd_amount * open_position.currency_quantity / -order.currency_quantity

    def close_portion_of_position(self, position_ix, order, open_position, unsold_quantity):
        self.df.loc[position_ix]['closed'] = True
        self.df.loc[position_ix]['sell_date'] = order.date
        self.df.loc[position_ix]['proceeds'] = order.usd_amount
        self.df.loc[position_ix]['cost_basis'] = open_position.cost_basis * unsold_quantity / open_position.currency_quantity
        self.df.loc[position_ix]['currency_quantity'] = unsold_quantity

        remainder_position = Position(
            currency=open_position.currency,
            purchase_date=open_position.purchase_date,
            cost_basis=open_position.cost_basis - self.df.loc[position_ix]['cost_basis'],
            currency_quantity=open_position.currency_quantity - unsold_quantity
        )
        self.add(remainder_position)

    def close_positions_to_complete_sale(self, order):
        open_positions = self.get_open_positions()
        quantity_to_sell = -order.currency_quantity
        for ix, open_position in open_positions.iterrows():
            if open_position.currency_quantity == quantity_to_sell:
                positions.close_position_equal_to_sale(ix, order)
                return
            elif open_position.currency_quantity > quantity_to_sell:
                positions.close_portion_of_position(ix, order, open_position, quantity_to_sell)
                return
            elif open_position.currency_quantity < quantity_to_sell:
                positions.close_position_as_fraction_of_sale(ix, order, open_position)
                quantity_to_sell -= open_position.currency_quantity
                if quantity_to_sell == 0:
                    return


raw_transactions = pd.read_csv('./coinbase_pro_transactions_2021.csv')

buy_sell_transactions = raw_transactions[
    (raw_transactions['order id'].isnull() == False) &
    (raw_transactions['type'] == 'match')
    ]

order_id_groups = buy_sell_transactions.groupby('order id', sort=False)
orders = pd.DataFrame(order_from_group_of_transaction_records(name, group) for name, group in order_id_groups)

positions = Positions()
for _, order in orders.iterrows():
    if order.order_type == 'buy':
        positions.create_open_position(order)
    else:
        positions.close_positions_to_complete_sale(order)

print("TOTAL COST BASIS:", round(positions.total_cost_basis, 2))
print("TOTAL PROCEEDS:", round(positions.total_proceeds, 2))
