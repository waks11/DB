from MARIADB_CREDS import DB_CONFIG
from mariadb import connect
from models.RentalHistory import RentalHistory
from models.Waitlist import Waitlist
from models.Item import Item
from models.Rental import Rental
from models.Customer import Customer
from datetime import date, timedelta


conn = connect(user=DB_CONFIG["username"], password=DB_CONFIG["password"], host=DB_CONFIG["host"],
               database=DB_CONFIG["database"], port=DB_CONFIG["port"])


cur = conn.cursor()


def add_item(new_item: Item = None):
    """
    new_item - An Item object containing a new item to be inserted into the DB in the item table.
        new_item and its attributes will never be None.
    """
    cur.execute("SELECT COALESCE(MAX(i_item_sk), 0) + 1 FROM item")
    new_sk = cur.fetchone()[0]

    rec_date = f"{new_item.start_year}-01-01"

    cur.execute(
        "INSERT INTO item (i_item_sk, i_item_id, i_rec_start_date, i_product_name, "
        "i_brand, i_category, i_manufact, i_current_price, i_num_owned) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (new_sk, new_item.item_id, rec_date, new_item.product_name,
         new_item.brand, new_item.category, new_item.manufact,
         new_item.current_price, new_item.num_owned)
    )


def add_customer(new_customer: Customer = None):
    """
    new_customer - A Customer object containing a new customer to be inserted into the DB in the customer table.
        new_customer and its attributes will never be None.
    """
    # Address format: "{street_number} {street_name}, {city}, {state} {zip}"
    street_full, city, state_zip = new_customer.address.split(", ")
    street_number, street_name = street_full.split(" ", 1)
    state, zip_code = state_zip.split(" ", 1)

    cur.execute("SELECT COALESCE(MAX(ca_address_sk), 0) + 1 FROM customer_address")
    new_addr_sk = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO customer_address (ca_address_sk, ca_street_number, ca_street_name, "
        "ca_city, ca_state, ca_zip) VALUES (?, ?, ?, ?, ?, ?)",
        (new_addr_sk, street_number, street_name, city, state, zip_code)
    )

    first_name, last_name = new_customer.name.split(" ", 1)

    cur.execute("SELECT COALESCE(MAX(c_customer_sk), 0) + 1 FROM customer")
    new_cust_sk = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO customer (c_customer_sk, c_customer_id, c_first_name, c_last_name, "
        "c_email_address, c_current_addr_sk) VALUES (?, ?, ?, ?, ?, ?)",
        (new_cust_sk, new_customer.customer_id, first_name, last_name,
         new_customer.email, new_addr_sk)
    )


def edit_customer(original_customer_id: str = None, new_customer: Customer = None):
    """
    original_customer_id - A string containing the customer id for the customer to be edited.
    new_customer - A Customer object containing attributes to update. If an attribute is None, it should not be altered.
    """
    raise NotImplementedError("you must implement this function")


def rent_item(item_id: str = None, customer_id: str = None):
    """
    item_id - A string containing the Item ID for the item being rented.
    customer_id - A string containing the customer id of the customer renting the item.
    """
    raise NotImplementedError("you must implement this function")


def waitlist_customer(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's new place in line.
    """
    raise NotImplementedError("you must implement this function")

def update_waitlist(item_id: str = None):
    """
    Removes person at position 1 and shifts everyone else down by 1.
    """
    raise NotImplementedError("you must implement this function")


def return_item(item_id: str = None, customer_id: str = None):
    """
    Moves a rental from rental to rental_history with return_date = today.
    """
    raise NotImplementedError("you must implement this function")


def grant_extension(item_id: str = None, customer_id: str = None):
    """
    Adds 14 days to the due_date.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_items(filter_attributes: Item = None,
                       use_patterns: bool = False,
                       min_price: float = -1,
                       max_price: float = -1,
                       min_start_year: int = -1,
                       max_start_year: int = -1) -> list[Item]:
    """
    Returns a list of Item objects matching the filters.
    """
    where = []
    params = []
    op = "LIKE" if use_patterns else "="

    if filter_attributes is not None:
        if filter_attributes.item_id is not None:
            where.append(f"i_item_id {op} ?")
            params.append(filter_attributes.item_id)
        if filter_attributes.product_name is not None:
            where.append(f"i_product_name {op} ?")
            params.append(filter_attributes.product_name)
        if filter_attributes.brand is not None:
            where.append(f"i_brand {op} ?")
            params.append(filter_attributes.brand)
        if filter_attributes.category is not None:
            where.append(f"i_category {op} ?")
            params.append(filter_attributes.category)
        if filter_attributes.manufact is not None:
            where.append(f"i_manufact {op} ?")
            params.append(filter_attributes.manufact)
        if filter_attributes.current_price != -1:
            where.append("i_current_price = ?")
            params.append(filter_attributes.current_price)
        if filter_attributes.start_year != -1:
            where.append("YEAR(i_rec_start_date) = ?")
            params.append(filter_attributes.start_year)
        if filter_attributes.num_owned != -1:
            where.append("i_num_owned = ?")
            params.append(filter_attributes.num_owned)

    if min_price != -1:
        where.append("i_current_price >= ?")
        params.append(min_price)
    if max_price != -1:
        where.append("i_current_price <= ?")
        params.append(max_price)
    if min_start_year != -1:
        where.append("YEAR(i_rec_start_date) >= ?")
        params.append(min_start_year)
    if max_start_year != -1:
        where.append("YEAR(i_rec_start_date) <= ?")
        params.append(max_start_year)

    sql = ("SELECT i_item_id, i_product_name, i_brand, i_category, i_manufact, "
           "i_current_price, YEAR(i_rec_start_date), i_num_owned FROM item")
    if where:
        sql += " WHERE " + " AND ".join(where)

    cur.execute(sql, params)
    rows = cur.fetchall()

    items = []
    for r in rows:
        items.append(Item(
            item_id=r[0].strip() if r[0] is not None else None,
            product_name=r[1].strip() if r[1] is not None else None,
            brand=r[2].strip() if r[2] is not None else None,
            category=r[3].strip() if r[3] is not None else None,
            manufact=r[4].strip() if r[4] is not None else None,
            current_price=float(r[5]) if r[5] is not None else -1,
            start_year=int(r[6]) if r[6] is not None else -1,
            num_owned=int(r[7]) if r[7] is not None else -1,
        ))
    return items


def get_filtered_customers(filter_attributes: Customer = None, use_patterns: bool = False) -> list[Customer]:
    """
    Returns a list of Customer objects matching the filters.
    """
    where = []
    params = []
    op = "LIKE" if use_patterns else "="

    name_expr = "CONCAT(TRIM(c_first_name), ' ', TRIM(c_last_name))"
    addr_expr = ("CONCAT(TRIM(ca_street_number), ' ', TRIM(ca_street_name), ', ', "
                 "TRIM(ca_city), ', ', TRIM(ca_state), ' ', TRIM(ca_zip))")

    if filter_attributes is not None:
        if filter_attributes.customer_id is not None:
            where.append(f"c_customer_id {op} ?")
            params.append(filter_attributes.customer_id)
        if filter_attributes.name is not None:
            where.append(f"{name_expr} {op} ?")
            params.append(filter_attributes.name)
        if filter_attributes.address is not None:
            where.append(f"{addr_expr} {op} ?")
            params.append(filter_attributes.address)
        if filter_attributes.email is not None:
            where.append(f"c_email_address {op} ?")
            params.append(filter_attributes.email)

    sql = ("SELECT c_customer_id, "
           f"{name_expr}, "
           f"{addr_expr}, "
           "c_email_address "
           "FROM customer LEFT JOIN customer_address ON c_current_addr_sk = ca_address_sk")
    if where:
        sql += " WHERE " + " AND ".join(where)

    cur.execute(sql, params)
    rows = cur.fetchall()

    customers = []
    for r in rows:
        customers.append(Customer(
            customer_id=r[0].strip() if r[0] is not None else None,
            name=r[1].strip() if r[1] is not None else None,
            address=r[2].strip() if r[2] is not None else None,
            email=r[3].strip() if r[3] is not None else None,
        ))
    return customers


def get_filtered_rentals(filter_attributes: Rental = None,
                         min_rental_date: str = None,
                         max_rental_date: str = None,
                         min_due_date: str = None,
                         max_due_date: str = None) -> list[Rental]:
    """
    Returns a list of Rental objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_rental_histories(filter_attributes: RentalHistory = None,
                                  min_rental_date: str = None,
                                  max_rental_date: str = None,
                                  min_due_date: str = None,
                                  max_due_date: str = None,
                                  min_return_date: str = None,
                                  max_return_date: str = None) -> list[RentalHistory]:
    """
    Returns a list of RentalHistory objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    Returns a list of Waitlist objects matching the filters.
    """
    raise NotImplementedError("you must implement this function")


def number_in_stock(item_id: str = None) -> int:
    """
    Returns num_owned - active rentals. Returns -1 if item doesn't exist.
    """
    cur.execute("SELECT i_num_owned FROM item WHERE i_item_id = ?", (item_id,))
    row = cur.fetchone()
    if row is None:
        return -1

    num_owned = row[0]
    cur.execute("SELECT COUNT(*) FROM rental WHERE item_id = ?", (item_id,))
    active = cur.fetchone()[0]
    return num_owned - active


def place_in_line(item_id: str = None, customer_id: str = None) -> int:
    """
    Returns the customer's place_in_line, or -1 if not on waitlist.
    """
    raise NotImplementedError("you must implement this function")


def line_length(item_id: str = None) -> int:
    """
    Returns how many people are on the waitlist for this item.
    """
    raise NotImplementedError("you must implement this function")


def save_changes():
    """
    Commits all changes made to the db.
    """
    conn.commit()


def close_connection():
    """
    Closes the cursor and connection.
    """
    cur.close()
    conn.close()

