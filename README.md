# Coinbase Pro Tax Calculator
For determining cost basis and proceeds for crypto trades within Coinbase Pro.

Used for the year 2021.  Use at your own risk.

## Assumptions
- No transactions occurred prior to 2021 (2021 is first year of trading) 
- All transactions are short-term (or of the same class)
- First-in First-out calculation

## Dependencies
- `poetry` (loose, can probably use pip or something. See `pyproject.toml` for python dependencies)
- `python ^3.10` (should work with older versions too)

Installing dependencies:
```shell
poetry install
```

## Inputs
The input to this calculator is a generated account statement.  From the Coinbase Pro web interface:
- Profile -> Statements
- Generate -> Account
- Download file as csv

Rename the file to `coinbase_pro_transactions.csv`

## Running the Calculator
```sh
poetry run python calculate_taxes.py
```

## Outputs
The calculator prints to the terminal:
- Total Cost Basis: The sum of the cost basis for all closed positions
- Total Proceeds: The sum of all proceeds for all closed positions

Positions that remain open are not factored into the total cost basis.

## Future Desired Features
- Handle positions that were opened prior to the year of interest
  - Will be needed for 2022
- Compute using a FILO method