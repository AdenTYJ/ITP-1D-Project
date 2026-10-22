## Business Logic ---------------------------------------------------------------------
## This file stores functions that implement the business logic.
## 1) calculate_total: Takes in the number of adults and children and returns
## the total price for adults and the total price for children.
##
## 2) audio_guides: Takes in the number of items and returns their total price.
## ------------------------------------------------------------------------------------

def calculate_total(adults, children):
    ADULT_PRICE = 10
    CHILD_PRICE = 5

    adults_total = adults * ADULT_PRICE
    children_total = children * CHILD_PRICE

    return adults_total, children_total

def audio_guides(items):
    PRICE_PER_ITEM = 3

    total_price = items * PRICE_PER_ITEM

    return total_price

def ticket_type_price(ticket_type):
    if ticket_type == "Peak":
        return 5
    elif ticket_type == "Off-Peak":
        return 2
    else:
        return 0

## Make It Yours ---------------------------------------------------------------------
## You are now ready to design your own ticketing scheme 
## And modify the code so that the web application works according to your design. 
## ------------------------------------------------------------------------------------