"""
Family Office Platform - Data Formatters

Provides formatting functions for currency, percentages, dates, and
structured data presentation.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union


def format_currency(
    value: Union[Decimal, float, int, str],
    currency_symbol: str = '$',
    decimal_places: int = 2,
    thousands_separator: str = ',',
    negative_format: str = 'parentheses'
) -> str:
    """
    Format a numeric value as currency.

    Args:
        value: Value to format
        currency_symbol: Currency symbol (default '$')
        decimal_places: Number of decimal places (default 2)
        thousands_separator: Separator for thousands (default ',')
        negative_format: How to format negatives ('parentheses' or 'minus')

    Returns:
        Formatted currency string
    """
    if value is None:
        return f"{currency_symbol}0.00"

    try:
        decimal_value = Decimal(str(value))
    except:
        return f"{currency_symbol}0.00"

    is_negative = decimal_value < 0
    decimal_value = abs(decimal_value)

    # Round to decimal places
    quantize_str = '0.' + '0' * decimal_places if decimal_places > 0 else '0'
    rounded = decimal_value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    # Format with thousands separator
    parts = str(rounded).split('.')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else '00'

    # Add thousands separators
    integer_with_sep = ''
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            integer_with_sep = thousands_separator + integer_with_sep
        integer_with_sep = digit + integer_with_sep

    formatted = f"{currency_symbol}{integer_with_sep}.{decimal_part}"

    if is_negative:
        if negative_format == 'parentheses':
            formatted = f"({formatted})"
        else:
            formatted = f"-{formatted}"

    return formatted


def format_percentage(
    value: Union[Decimal, float, int, str],
    decimal_places: int = 2,
    multiply_by_100: bool = True,
    include_sign: bool = True
) -> str:
    """
    Format a numeric value as percentage.

    Args:
        value: Value to format (e.g., 0.15 for 15%)
        decimal_places: Number of decimal places
        multiply_by_100: Whether to multiply by 100 (True if value is decimal like 0.15)
        include_sign: Whether to include + for positive values

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "0.00%"

    try:
        decimal_value = Decimal(str(value))
    except:
        return "0.00%"

    if multiply_by_100:
        decimal_value *= 100

    # Round to decimal places
    quantize_str = '0.' + '0' * decimal_places if decimal_places > 0 else '0'
    rounded = decimal_value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    sign = ''
    if include_sign and rounded > 0:
        sign = '+'

    return f"{sign}{rounded}%"


def format_decimal(
    value: Union[Decimal, float, int, str],
    decimal_places: int = 6,
    strip_trailing_zeros: bool = False
) -> str:
    """
    Format a decimal value with specified precision.

    Args:
        value: Value to format
        decimal_places: Number of decimal places
        strip_trailing_zeros: Whether to remove trailing zeros

    Returns:
        Formatted decimal string
    """
    if value is None:
        return "0"

    try:
        decimal_value = Decimal(str(value))
    except:
        return "0"

    # Round to decimal places
    quantize_str = '0.' + '0' * decimal_places if decimal_places > 0 else '0'
    rounded = decimal_value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)

    result = str(rounded)

    if strip_trailing_zeros and '.' in result:
        result = result.rstrip('0').rstrip('.')

    return result


def format_date(
    value: Union[date, datetime, str],
    format_string: str = '%Y-%m-%d',
    relative: bool = False
) -> str:
    """
    Format a date value.

    Args:
        value: Date to format
        format_string: strftime format string
        relative: Whether to show relative time (e.g., "2 days ago")

    Returns:
        Formatted date string
    """
    if value is None:
        return ""

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value

    if isinstance(value, datetime):
        dt = value
        d = value.date()
    else:
        dt = datetime.combine(value, datetime.min.time())
        d = value

    if relative:
        now = datetime.now()
        if isinstance(value, date) and not isinstance(value, datetime):
            now = now.date()
            diff = now - d
        else:
            diff = now - dt

        days = diff.days
        seconds = diff.seconds if hasattr(diff, 'seconds') else 0

        if days == 0:
            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif days == 1:
            return "yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"

    if isinstance(value, datetime):
        return value.strftime(format_string)
    else:
        return value.strftime(format_string)


def format_large_number(
    value: Union[Decimal, float, int, str],
    decimal_places: int = 1
) -> str:
    """
    Format large numbers with K, M, B suffixes.

    Args:
        value: Number to format
        decimal_places: Decimal places to show

    Returns:
        Formatted string (e.g., "1.5M", "250K")
    """
    if value is None:
        return "0"

    try:
        num = float(value)
    except:
        return "0"

    is_negative = num < 0
    num = abs(num)

    if num >= 1_000_000_000:
        formatted = f"{num / 1_000_000_000:.{decimal_places}f}B"
    elif num >= 1_000_000:
        formatted = f"{num / 1_000_000:.{decimal_places}f}M"
    elif num >= 1_000:
        formatted = f"{num / 1_000:.{decimal_places}f}K"
    else:
        formatted = f"{num:.{decimal_places}f}"

    # Remove unnecessary decimals
    if '.' in formatted:
        formatted = formatted.rstrip('0').rstrip('.')
        # Add back suffix if stripped
        for suffix in ['B', 'M', 'K']:
            if suffix in str(value) or num >= {'B': 1e9, 'M': 1e6, 'K': 1e3}.get(suffix, 0):
                if not formatted.endswith(suffix) and suffix in f"{num / {'B': 1e9, 'M': 1e6, 'K': 1e3}[suffix]:.{decimal_places}f}{suffix}":
                    pass

    if is_negative:
        formatted = f"-{formatted}"

    return formatted


def format_portfolio_summary(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Format a portfolio summary for display.

    Args:
        data: Raw portfolio data dictionary

    Returns:
        Dictionary with formatted values
    """
    formatted = {}

    # Format monetary values
    monetary_fields = [
        'net_worth', 'total_assets', 'total_liabilities',
        'cash', 'investments', 'real_estate', 'vehicles',
        'startup_equity', 'personal_property', 'current_value',
        'cost_basis', 'unrealized_gain_loss'
    ]

    for field in monetary_fields:
        if field in data:
            formatted[field] = format_currency(data[field])
            formatted[f'{field}_raw'] = data[field]

    # Format percentage values
    percentage_fields = [
        'total_return', 'daily_return', 'monthly_return', 'annual_return',
        'alpha', 'volatility', 'sharpe_ratio'
    ]

    for field in percentage_fields:
        if field in data:
            formatted[field] = format_percentage(data[field])
            formatted[f'{field}_raw'] = data[field]

    # Format beta (not a percentage)
    if 'beta' in data:
        formatted['beta'] = format_decimal(data['beta'], decimal_places=2)
        formatted['beta_raw'] = data['beta']

    # Format dates
    date_fields = ['last_updated', 'as_of_date', 'created_at']
    for field in date_fields:
        if field in data:
            formatted[field] = format_date(data[field], relative=True)
            formatted[f'{field}_formatted'] = format_date(data[field], '%B %d, %Y')

    # Pass through string fields
    string_fields = ['user_id', 'account_name', 'symbol', 'name', 'asset_type']
    for field in string_fields:
        if field in data:
            formatted[field] = data[field]

    return formatted


def format_asset_allocation(allocations: Dict[str, Decimal]) -> List[Dict[str, Any]]:
    """
    Format asset allocation data for charts.

    Args:
        allocations: Dictionary of {asset_type: value}

    Returns:
        List of formatted allocation entries
    """
    total = sum(allocations.values())
    if total == 0:
        return []

    result = []
    colors = {
        'cash': '#28a745',
        'investments': '#007bff',
        'real_estate': '#ffc107',
        'vehicles': '#6c757d',
        'startup_equity': '#17a2b8',
        'personal_property': '#dc3545',
        'stocks': '#007bff',
        'bonds': '#28a745',
        'etf': '#6610f2',
        'mutual_fund': '#fd7e14',
        'crypto': '#e83e8c',
        'other': '#6c757d'
    }

    for asset_type, value in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
        percentage = (value / total) * 100
        result.append({
            'type': asset_type,
            'label': asset_type.replace('_', ' ').title(),
            'value': float(value),
            'value_formatted': format_currency(value),
            'percentage': float(percentage),
            'percentage_formatted': format_percentage(percentage / 100, multiply_by_100=True, include_sign=False),
            'color': colors.get(asset_type.lower(), '#6c757d')
        })

    return result


def format_transaction_history(transactions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Format transaction history for display.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        List of formatted transaction dictionaries
    """
    formatted = []

    for tx in transactions:
        formatted_tx = {
            'id': tx.get('id', ''),
            'date': format_date(tx.get('transaction_date'), '%b %d, %Y'),
            'type': tx.get('transaction_type', '').title(),
            'symbol': tx.get('symbol', ''),
            'quantity': format_decimal(tx.get('quantity', 0), decimal_places=4, strip_trailing_zeros=True),
            'price': format_currency(tx.get('price', 0)),
            'total': format_currency(tx.get('total_amount', 0)),
            'fees': format_currency(tx.get('fees', 0))
        }
        formatted.append(formatted_tx)

    return formatted
