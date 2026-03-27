import database
import sheet


def parse_outcome_amount(amount: str) -> float | None:
    amount = amount.replace(",", ".")
    if amount[0] == "+" or amount[0] == "-":
        amount = amount[1:]
    amount = "-" + amount
    try:
        float(amount)
    except ValueError:
        return None
    return float(amount)


def parse_income_amount(amount: str) -> float | None:
    amount = amount.replace(",", ".")
    if amount[0] == "-":
        amount = amount[1:]
    try:
        float(amount)
    except ValueError:
        return None
    return float(amount)


def _parse_account(account: str, sheet_data) -> str | None:
    account_list = sheet_data["accounts"]
    for i in range(len(account_list)):
        if account.lower() == account_list[i].lower():
            account = account_list[i]
            return account
    return None


def _parse_outcome_category(category: str, sheet_data: dict) -> str | None:
    category_list = sheet_data["outcome categories"]
    for i in range(len(category_list)):
        if category.lower() == category_list[i].lower():
            category = category_list[i]
            return category
    return None


def _parse_income_category(category: str, sheet_data: dict) -> str | None:
    category_list = sheet_data["income categories"]
    for i in range(len(category_list)):
        if category.lower() == category_list[i].lower():
            category = category_list[i]
            return category
    return None


def parse_record(raw_record: list, user_id: str, type: str) -> list:
    for arg in range(len(raw_record)):
        raw_record[arg] = raw_record[arg].strip()

    parsed_data = []
    user_sheet = sheet.Sheet(database.get_sheet_id(user_id))
    sheet_data = user_sheet.get_day_categories_accounts()
    match raw_record:
        case amount, category, account, description:
            if type == "income":
                amount = parse_income_amount(amount)
                category = _parse_income_category(category, sheet_data)
            else:
                amount = parse_outcome_amount(amount)
                category = _parse_outcome_category(category, sheet_data)
            account = _parse_account(account, sheet_data)
            parsed_data = [sheet_data["today"], description, category, amount, account]

        case amount, category, account:
            if type == "income":
                amount = parse_income_amount(amount)
                category = _parse_income_category(category, sheet_data)
            elif type == "outcome":
                amount = parse_outcome_amount(amount)
                category = _parse_outcome_category(category, sheet_data)
            account = _parse_account(account, sheet_data)
            parsed_data = [sheet_data["today"], "", category, amount, account]

        case amount, category:
            if type == "income":
                amount = parse_income_amount(amount)
                category = _parse_income_category(category, sheet_data)
            else:
                amount = parse_outcome_amount(amount)
                category = _parse_outcome_category(category, sheet_data)
            parsed_data = [sheet_data["today"], "", category, amount, ""]
    return parsed_data


def parse_transaction(raw_transaction: list, user_id: str) -> list:
    for arg in range(len(raw_transaction)):
        raw_transaction[arg] = raw_transaction[arg].strip()

    parsed_data = []

    # Getting account list from sheet
    user_sheet = sheet.Sheet(database.get_sheet_id(user_id))
    sheet_data = user_sheet.get_day_accounts()

    match raw_transaction:
        case outcome_amount, outcome_account, income_amount, income_account:
            outcome_amount = parse_outcome_amount(outcome_amount)
            outcome_account = _parse_account(outcome_account, sheet_data)
            income_amount = parse_income_amount(income_amount)
            income_account = _parse_account(income_account, sheet_data)

            parsed_data = [
                outcome_amount,
                outcome_account,
                income_amount,
                income_account,
            ]
            parsed_data.insert(0, sheet_data["today"])

        case outcome_amount, outcome_account, income_account:
            outcome_amount = parse_outcome_amount(outcome_amount)
            outcome_account = _parse_account(outcome_account, sheet_data)
            income_amount = parse_income_amount(raw_transaction[0])
            income_account = _parse_account(income_account, sheet_data)

            parsed_data = [
                outcome_amount,
                outcome_account,
                income_amount,
                income_account,
            ]
            parsed_data.insert(0, sheet_data["today"])

    return parsed_data


def parse_shortcut_record(text: str, user_id: str) -> dict | None:
    """
    Parse shortcut format: -50k jajan cash optional description
    
    Format:
    - First char: - (expense) or + (income)
    - Amount with k/m support: 50k, 100, 1.5m
    - Second word: category
    - Third word: account
    - Remaining: description (optional)
    
    Returns dict with parsed data or error payload
    """
    text = text.strip()
    
    # Check if starts with + or -
    if not text or text[0] not in ['+', '-']:
        return None
    
    record_type = "income" if text[0] == '+' else "outcome"
    text = text[1:].strip()
    
    # Split by spaces
    parts = text.split(maxsplit=3)
    if len(parts) < 3:
        return {"error": "invalid_format"}
    
    amount_str, category_str, account_str = parts[0], parts[1], parts[2]
    description = parts[3] if len(parts) > 3 else ""
    
    # Parse amount (50k, 100, 1.5m)
    try:
        amount_str = amount_str.replace(",", ".")
        if amount_str.lower().endswith('k'):
            amount = float(amount_str[:-1]) * 1000
        elif amount_str.lower().endswith('m'):
            amount = float(amount_str[:-1]) * 1000000
        else:
            amount = float(amount_str)
    except ValueError:
        return {"error": "invalid_amount"}
    
    # Get sheet data for category validation
    try:
        user_sheet = sheet.Sheet(database.get_sheet_id(user_id))
        sheet_data = user_sheet.get_day_categories_accounts()
    except Exception:
        return {"error": "sheet_unavailable"}
    
    # Validate category
    if record_type == "income":
        category = _parse_income_category(category_str, sheet_data)
        if not category:
            return {
                "error": "unknown_category",
                "available": sheet_data["income categories"],
            }
    else:
        category = _parse_outcome_category(category_str, sheet_data)
        if not category:
            return {
                "error": "unknown_category",
                "available": sheet_data["outcome categories"],
            }
    
    account = _parse_account(account_str, sheet_data)
    if not account:
        return {
            "error": "unknown_account",
            "available": sheet_data["accounts"],
        }
    
    return {
        "type": record_type,
        "amount": amount,
        "category": category,
        "description": description,
        "account": account,
        "date": sheet_data["today"],
    }
