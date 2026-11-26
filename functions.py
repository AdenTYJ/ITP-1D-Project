"""Ticket pricing and persistent daily booking capacity."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

# INIT Constants for ticket pricing and database location.
ADULT_PRICE = 10
CHILD_PRICE = 5
GUIDE_PRICE = 3
EXPRESS_PRICE = 5
DAILY_CAPACITY = 100
DATABASE_PATH = Path(__file__).with_name("bookings.sqlite3")
SINGAPORE_TIME = timezone(timedelta(hours=8))


# Returns the current date in Singapore.
def singapore_date():
    return datetime.now(SINGAPORE_TIME).date().isoformat()


# Returns the total cost for adults and children, without any discounts or extras.
def calculate_total(adults, children):
    adults_total = adults * ADULT_PRICE
    children_total = children * CHILD_PRICE
    return adults_total, children_total

# Returns total number of visitors in booking
def number_of_visitors(adults, children):
    return adults + children

# Returns the total cost for audio guides, without any discounts or extras.
def audio_guides(items):
    total = items * GUIDE_PRICE
    return total

# Returns the price multiplier for the selected ticket type.
def ticket_type_price(ticket_type):
    if ticket_type == "Peak":
        return 1.5
    elif ticket_type == "Off-Peak":
        return 1.0
    else:
        raise ValueError("Please select Peak or Off-Peak.")

# Main Booking Calculator function, returns a dictionary of all costs and totals for the booking.
def calculate_booking(adults, children, guides, ticket_type, express):
    visitors = number_of_visitors(adults, children)
    for quantity in (adults, children, guides):
        if type(quantity) is not int or quantity < 0:
            raise ValueError("Quantities must be non-negative whole numbers.")
    if visitors == 0:
        raise ValueError("Please select at least one visitor.")

    # Work out each charge separately before adding them together.
    multiplier = ticket_type_price(ticket_type)
    adult_cost, child_cost = calculate_total(adults, children)
    adult_cost = round(adult_cost * multiplier, 2)
    child_cost = round(child_cost * multiplier, 2)
    guide_cost = round(audio_guides(guides) * multiplier, 2)
    express_cost = 0.0
    if express:
        express_cost = round(visitors * EXPRESS_PRICE * multiplier, 2)

    # Only one family pack gets a discount, even in a larger group.
    discount = 0.0
    if adults >= 2 and children >= 2:
        family_price = (2 * ADULT_PRICE + 2 * CHILD_PRICE) * multiplier
        discount = round(family_price * 0.2, 2)

    total = adult_cost + child_cost + guide_cost + express_cost - discount
    return {
        "adults": adults,
        "children": children,
        "guides": guides,
        "visitors": visitors,
        "ticket_type": ticket_type,
        "express": express,
        "adult_cost": adult_cost,
        "child_cost": child_cost,
        "guide_cost": guide_cost,
        "express_cost": express_cost,
        "family_discount": discount,
        "total": round(total, 2),
    }

# Install SQLite Viewer by Florian Klampfer in VSCode Extensions to view database contents (bookings.sqlite3)
def open_database(database_path):
    # Create the table the first time the app is used.
    connection = sqlite3.connect(database_path, timeout=10)
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS daily_tickets "
            "(booking_date TEXT PRIMARY KEY, sold INTEGER NOT NULL CHECK(sold >= 0))"
        )
    except sqlite3.Error:
        connection.close()
        raise
    return connection

# Check remaining daily tickets SELECT sold from daily tickets (which is the primary key) WHERE (today's date) and subtract from daily capacity fixed at 100 tickets
def remaining_tickets(database_path=DATABASE_PATH, booking_date=None):
    if booking_date is None:
        booking_date = singapore_date()
    day = booking_date
    connection = open_database(database_path)
    try:
        row = connection.execute(
            "SELECT sold FROM daily_tickets WHERE booking_date = ?", (day,)
        ).fetchone()
        sold = 0
        if row is not None:
            sold = row[0]
        return DAILY_CAPACITY - sold
    finally:
        connection.close()


def confirm_booking(visitors, database_path=DATABASE_PATH, booking_date=None):
    if type(visitors) is not int or visitors <= 0:
        raise ValueError("Please select at least one visitor.")
    connection = open_database(database_path)
    try:
        with connection:
            # Lock updates until this booking finishes so two users cannot
            # buy the same last ticket. The with block saves or rolls back.
            connection.execute("BEGIN IMMEDIATE")
            if booking_date is None:
                booking_date = singapore_date()
            day = booking_date
            connection.execute(
                "INSERT OR IGNORE INTO daily_tickets (booking_date, sold) VALUES (?, 0)",
                (day,),
            )
            sold = connection.execute(
                "SELECT sold FROM daily_tickets WHERE booking_date = ?", (day,)
            ).fetchone()[0]
            remaining = DAILY_CAPACITY - sold
            if visitors > remaining:
                raise ValueError(f"Only {remaining} tickets remain for today.")
            connection.execute(
                "UPDATE daily_tickets SET sold = sold + ? WHERE booking_date = ?",
                (visitors, day),
            )
        return day
    finally:
        connection.close()
