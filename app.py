import math
import sqlite3
import time
import streamlit as st
import functions


# Only this part of the page refreshes every second.
@st.fragment(run_every=1)
def show_countdown():
    expires_at = st.session_state.quote_expires_at
    if expires_at is None or st.session_state.confirmed_date is not None:
        return

    seconds_left = math.ceil(expires_at - time.time())
    if seconds_left <= 0:
        # Refresh the full page so the expiry check removes the quotation.
        st.rerun()
        return

    minutes = seconds_left // 60
    seconds = seconds_left % 60
    st.metric("Time left to confirm", f"{minutes:02d}:{seconds:02d}")


#Main ticketing page, shows prices, takes input
st.title("The GOATS Tickets")
st.write("Adults: $10 | Children: $5 | Audio guides: $3 | Express: $5 per visitor")
st.caption("Peak prices are 1.5× for all items. One family pack (2 adults + 2 children) receives 20% off admission per booking.")
adults = st.number_input("Number of adults", min_value=0, max_value=10, step=1, key="adults")
children = st.number_input("Number of children", min_value=0, max_value=10, step=1, key="children")
guides = st.number_input("How many audio guides do you want to rent?", min_value=0, max_value=functions.number_of_visitors(adults, children), step=1, key="rental")
ticket_type = st.radio("Type of Ticket", ["Peak", "Off-Peak"])
express = st.checkbox("Express passes for all visitors")

today = functions.singapore_date()
# Streamlit runs this file again whenever a widget changes.
# Session state remembers the quote and confirmation between runs.
inputs = {
    "adults": adults,
    "children": children,
    "guides": guides,
    "ticket_type": ticket_type,
    "express": express,
    "date": today,
}
# A changed booking or new calendar day requires a fresh quotation.
if st.session_state.get("booking_inputs") != inputs:
    st.session_state.booking_inputs = inputs
    st.session_state.quote = None
    st.session_state.confirmed_date = None
    st.session_state.quote_expires_at = None

capacity_available = True
try:
    remaining = functions.remaining_tickets(booking_date=today)
    st.write(f"Tickets remaining today ({today}, Singapore): {remaining}/{functions.DAILY_CAPACITY}")
except sqlite3.Error:
    capacity_available = False
    st.error("Unable to access the booking database. Please try again later.")

if st.button("Get Total"):
    try:
        quote = functions.calculate_booking(adults, children, guides, ticket_type, express)
        if capacity_available and not st.session_state.confirmed_date and quote["visitors"] > remaining:
            raise ValueError(f"Only {remaining} tickets remain for today.")
        st.session_state.quote = quote
        if st.session_state.confirmed_date is None:
            # Five minutes is 300 seconds. Remember when this quote expires.
            st.session_state.quote_expires_at = time.time() + 300
    except ValueError as error:
        st.session_state.quote = None
        st.session_state.quote_expires_at = None
        st.error(str(error))

# Check expiry on each rerun, including when Confirm Booking is clicked.
# Confirmed bookings stay valid after the quotation timer ends.
if st.session_state.quote is not None and st.session_state.confirmed_date is None:
    expires_at = st.session_state.get("quote_expires_at")
    if expires_at is None or time.time() >= expires_at:
        st.session_state.quote = None
        st.session_state.quote_expires_at = None
        st.warning("Your quotation has expired. Please click Get Total for a new quotation.")

quote = st.session_state.quote
if quote is not None:
    already_confirmed = st.session_state.confirmed_date is not None
    disable_confirmation = not capacity_available or already_confirmed
    if not already_confirmed:
        show_countdown()
    if st.button("Confirm Booking", disabled=disable_confirmation):
        try:
            st.session_state.confirmed_date = functions.confirm_booking(quote["visitors"])
            st.session_state.quote_expires_at = None
            st.rerun()
        except ValueError as error:
            st.error(str(error))
        except sqlite3.Error:
            st.error("Unable to save your booking. Your booking has not been confirmed. Please try again later.")

    confirmed_date = st.session_state.confirmed_date
    express_text = "No"
    if quote["express"]:
        express_text = "Yes"

    booking_status = "Quotation"
    booking_date = today
    if confirmed_date is not None:
        booking_status = "Confirmed"
        booking_date = confirmed_date

    receipt = {
        "Adults": quote["adults"],
        "Children": quote["children"],
        "Audio guides": quote["guides"],
        "Ticket period": quote["ticket_type"],
        "Express passes": express_text,
        "Adult admission": f'${quote["adult_cost"]:.2f}',
        "Child admission": f'${quote["child_cost"]:.2f}',
        "Audio guide charge": f'${quote["guide_cost"]:.2f}',
        "Express charge": f'${quote["express_cost"]:.2f}',
        "Family savings": f'${quote["family_discount"]:.2f}',
        "Total": f'${quote["total"]:.2f}',
        "Booking date": booking_date,
        "Booking status": booking_status,
    }
    # Every value is text so the table can display numbers and labels together.
    rows = []
    for item, value in receipt.items():
        rows.append({"Item": item, "Details": str(value)})
    st.table(rows)
    if confirmed_date:
        st.success("Booking confirmed. Payment has not been processed.")
else:
    st.info("Choose your quantities and select Get Total to see a quotation.")
