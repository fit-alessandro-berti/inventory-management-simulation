import sqlite3
import random
from datetime import datetime, timedelta

def create_tables(conn):
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute('PRAGMA foreign_keys = ON;')

    # Create table: Sales Order Documents
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SalesOrderDocuments (
        sales_document_number INTEGER PRIMARY KEY,
        document_creation_date DATE,
        customer_number INTEGER,
        document_date_in_document DATE,
        sales_document_type TEXT,
        order_type TEXT,
        order_reason TEXT
    );
    ''')

    # Create table: Sales Order Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SalesOrderItems (
        sales_document_number INTEGER,
        item_number INTEGER,
        material_number INTEGER,
        plant TEXT,
        order_quantity REAL,
        net_price REAL,
        PRIMARY KEY (sales_document_number, item_number),
        FOREIGN KEY (sales_document_number) REFERENCES SalesOrderDocuments(sales_document_number),
        FOREIGN KEY (material_number) REFERENCES Materials(material_number)
    );
    ''')

    # Create table: Materials
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Materials (
        material_number INTEGER PRIMARY KEY,
        material_type TEXT,
        industry_sector TEXT,
        material_group TEXT,
        valuation_class TEXT,
        gross_weight REAL,
        net_weight REAL,
        weight_unit TEXT,
        volume REAL,
        volume_unit TEXT,
        transport_group TEXT
    );
    ''')

    # Create table: Purchase Requisitions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PurchaseRequisitions (
        client TEXT,
        purchase_document_number INTEGER,
        item_number_of_purchasing_document INTEGER,
        purchase_requisition_number INTEGER PRIMARY KEY,
        purchase_requisition_item INTEGER,
        purchase_requisition_date DATE,
        document_type TEXT,
        purchasing_document_category TEXT,
        planned_delivery_time INTEGER,
        latest_possible_goods_receipt DATE,
        quantity REAL,
        unit_of_measure TEXT
    );
    ''')

    # Create table: Material Stocks
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MaterialStocks (
        client TEXT,
        material_number INTEGER,
        plant TEXT,
        storage_location TEXT,
        stock_in_quality_inspection REAL,
        stock_in_transfer REAL,
        stock_in_posting REAL,
        stock_of_material_provided_to_vendor REAL,
        blocked_stock REAL,
        returns_stock REAL,
        PRIMARY KEY (material_number, plant, storage_location),
        FOREIGN KEY (material_number) REFERENCES Materials(material_number)
    );
    ''')

    # Create table: Goods Receipts and Issues
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS GoodsReceiptsAndIssues (
        client TEXT,
        purchase_document_number INTEGER,
        line_item_in_purchase_document INTEGER,
        sequential_number_of_account_assignment INTEGER,
        movement_type TEXT,
        fiscal_year INTEGER,
        document_number INTEGER,
        accounting_document_line INTEGER,
        material_number INTEGER,
        plant TEXT,
        reference_document_number INTEGER,
        document_date_in_document DATE,
        posting_date_in_the_document DATE,
        date_of_the_posting_in_the_document DATE,
        time_of_the_posting_in_the_document TEXT,  -- Changed from TIME to TEXT
        quantity REAL,
        FOREIGN KEY (material_number) REFERENCES Materials(material_number)
    );
    ''')

    # Create table: Sales Document Flows
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SalesDocumentFlows (
        client TEXT,
        sales_document INTEGER,
        sales_document_item INTEGER,
        subsequent_sales_document INTEGER,
        subsequent_sales_document_item INTEGER,
        document_category_of_subsequent_document TEXT,
        document_category_of_preceding_document TEXT,
        document_date DATE,
        PRIMARY KEY (sales_document, sales_document_item, subsequent_sales_document, subsequent_sales_document_item),
        FOREIGN KEY (sales_document) REFERENCES SalesOrderDocuments(sales_document_number)
    );
    ''')

    # Create table: Purchase Order Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PurchaseOrderItems (
        purchase_order_number INTEGER,
        purchase_order_item_number INTEGER,
        material_number INTEGER,
        plant TEXT,
        quantity REAL,
        change_date DATE,
        net_price REAL,
        PRIMARY KEY (purchase_order_number, purchase_order_item_number),
        FOREIGN KEY (purchase_order_number) REFERENCES PurchaseOrderDocuments(purchase_document_number),
        FOREIGN KEY (material_number) REFERENCES Materials(material_number)
    );
    ''')

    # Create table: Purchase Order Documents
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PurchaseOrderDocuments (
        purchase_document_number INTEGER PRIMARY KEY,
        record_creation_date DATE,
        account_number_of_vendor INTEGER,
        purchase_order_date DATE,
        purchasing_document_category TEXT,
        purchasing_document_type TEXT,
        blocking_indicator BOOLEAN
    );
    ''')

    # Create table: Material Documents
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MaterialDocuments (
        client TEXT,
        material_document_number INTEGER,
        material_document_year INTEGER,
        line_item INTEGER,
        material_number INTEGER,
        plant TEXT,
        storage_location TEXT,
        vendors_account_number INTEGER,
        customer_number INTEGER,
        movement_type TEXT,
        receiving_plant TEXT,
        quantity REAL,
        posting_date_in_the_document DATE,
        PRIMARY KEY (material_document_number, material_document_year, line_item),
        FOREIGN KEY (material_number) REFERENCES Materials(material_number)
    );
    ''')

    # Create table: Order Suggestions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OrderSuggestions (
        order_number INTEGER,
        order_position INTEGER,
        article_number INTEGER,
        order_quantity REAL,
        date DATE,
        order_date DATE,
        delivery_date DATE,
        plant TEXT,
        PRIMARY KEY (order_number, order_position),
        FOREIGN KEY (article_number) REFERENCES Materials(material_number)
    );
    ''')

    conn.commit()

def populate_tables(conn):
    cursor = conn.cursor()

    # Generate Materials
    num_materials = 100
    materials = []
    for i in range(1, num_materials + 1):
        material_number = i
        material_type = random.choice(['RAW', 'FINISHED', 'SEMIFINISHED'])
        industry_sector = random.choice(['Automotive', 'Electronics', 'Pharmaceutical'])
        material_group = random.choice(['GroupA', 'GroupB', 'GroupC'])
        valuation_class = random.choice(['ValClass1', 'ValClass2', 'ValClass3'])
        gross_weight = round(random.uniform(1.0, 100.0), 2)
        net_weight = round(gross_weight * random.uniform(0.8, 1.0), 2)
        weight_unit = 'kg'
        volume = round(random.uniform(0.1, 10.0), 2)
        volume_unit = 'm3'
        transport_group = random.choice(['TG1', 'TG2', 'TG3'])
        materials.append((material_number, material_type, industry_sector, material_group,
                          valuation_class, gross_weight, net_weight, weight_unit,
                          volume, volume_unit, transport_group))

    cursor.executemany('''
        INSERT INTO Materials (material_number, material_type, industry_sector, material_group,
                               valuation_class, gross_weight, net_weight, weight_unit,
                               volume, volume_unit, transport_group)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', materials)

    conn.commit()

    # Generate Sales Order Documents
    num_customers = 50
    customers = list(range(1, num_customers + 1))

    num_sales_orders = 200
    sales_order_documents = []
    for i in range(1, num_sales_orders + 1):
        sales_document_number = i
        document_creation_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        customer_number = random.choice(customers)
        document_date_in_document = document_creation_date
        sales_document_type = random.choice(['TypeA', 'TypeB', 'TypeC'])
        order_type = random.choice(['Normal', 'Urgent', 'Backorder'])
        order_reason = random.choice(['Stock Replenishment', 'Special Order', 'Promotion'])
        sales_order_documents.append((sales_document_number, document_creation_date,
                                      customer_number, document_date_in_document,
                                      sales_document_type, order_type, order_reason))

    cursor.executemany('''
        INSERT INTO SalesOrderDocuments (sales_document_number, document_creation_date,
                                         customer_number, document_date_in_document,
                                         sales_document_type, order_type, order_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sales_order_documents)

    conn.commit()

    # Generate Sales Order Items
    sales_order_items = []
    for sales_order in sales_order_documents:
        sales_document_number = sales_order[0]
        num_items = random.randint(1, 5)
        for item_number in range(1, num_items + 1):
            material_number = random.randint(1, num_materials)
            plant = 'Plant' + str(random.randint(1, 5))
            order_quantity = random.randint(1, 100)
            net_price = round(random.uniform(10.0, 1000.0), 2)
            sales_order_items.append((sales_document_number, item_number, material_number,
                                      plant, order_quantity, net_price))

    cursor.executemany('''
        INSERT INTO SalesOrderItems (sales_document_number, item_number, material_number,
                                     plant, order_quantity, net_price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sales_order_items)

    conn.commit()

    # Generate Purchase Order Documents
    num_vendors = 30
    vendors = list(range(1, num_vendors + 1))
    num_purchase_orders = 150
    purchase_order_documents = []
    for i in range(1, num_purchase_orders + 1):
        purchase_document_number = i
        record_creation_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        account_number_of_vendor = random.choice(vendors)
        purchase_order_date = record_creation_date
        purchasing_document_category = random.choice(['Standard', 'Subcontracting', 'Consignment'])
        purchasing_document_type = random.choice(['POTypeA', 'POTypeB', 'POTypeC'])
        blocking_indicator = random.choice([True, False])
        purchase_order_documents.append((purchase_document_number, record_creation_date,
                                         account_number_of_vendor, purchase_order_date,
                                         purchasing_document_category, purchasing_document_type,
                                         blocking_indicator))

    cursor.executemany('''
        INSERT INTO PurchaseOrderDocuments (purchase_document_number, record_creation_date,
                                            account_number_of_vendor, purchase_order_date,
                                            purchasing_document_category, purchasing_document_type,
                                            blocking_indicator)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', purchase_order_documents)

    conn.commit()

    # Generate Purchase Order Items
    purchase_order_items = []
    for po in purchase_order_documents:
        purchase_order_number = po[0]
        num_items = random.randint(1, 5)
        for item_number in range(1, num_items + 1):
            material_number = random.randint(1, num_materials)
            plant = 'Plant' + str(random.randint(1, 5))
            quantity = random.randint(1, 100)
            change_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
            net_price = round(random.uniform(10.0, 1000.0), 2)
            purchase_order_items.append((purchase_order_number, item_number, material_number,
                                         plant, quantity, change_date, net_price))

    cursor.executemany('''
        INSERT INTO PurchaseOrderItems (purchase_order_number, purchase_order_item_number,
                                        material_number, plant, quantity, change_date, net_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', purchase_order_items)

    conn.commit()

    # Generate Goods Receipts and Issues
    goods_receipts_issues = []
    for _ in range(200):
        client = 'Client' + str(random.randint(1, 5))
        purchase_document_number = random.randint(1, 150)  # Assuming num_purchase_orders = 150
        line_item_in_purchase_document = random.randint(1, 5)
        sequential_number_of_account_assignment = random.randint(1, 1000)
        movement_type = random.choice(['Goods Receipt', 'Goods Issue'])
        fiscal_year = datetime.now().year
        document_number = random.randint(100000, 999999)
        accounting_document_line = random.randint(1, 10)
        material_number = random.randint(1, 100)  # Assuming num_materials = 100
        plant = 'Plant' + str(random.randint(1, 5))
        reference_document_number = random.randint(100000, 999999)
        document_date_in_document = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        posting_date_in_the_document = document_date_in_document
        date_of_the_posting_in_the_document = document_date_in_document
        time_of_the_posting_in_the_document = datetime.now().strftime('%H:%M:%S')  # Convert to string
        quantity = random.randint(1, 100)
        goods_receipts_issues.append((client, purchase_document_number, line_item_in_purchase_document,
                                      sequential_number_of_account_assignment, movement_type, fiscal_year,
                                      document_number, accounting_document_line, material_number, plant,
                                      reference_document_number, document_date_in_document,
                                      posting_date_in_the_document, date_of_the_posting_in_the_document,
                                      time_of_the_posting_in_the_document, quantity))

    cursor.executemany('''
        INSERT INTO GoodsReceiptsAndIssues (client, purchase_document_number, line_item_in_purchase_document,
                                            sequential_number_of_account_assignment, movement_type, fiscal_year,
                                            document_number, accounting_document_line, material_number, plant,
                                            reference_document_number, document_date_in_document,
                                            posting_date_in_the_document, date_of_the_posting_in_the_document,
                                            time_of_the_posting_in_the_document, quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', goods_receipts_issues)

    conn.commit()

    # Generate Material Documents
    material_documents = []
    for _ in range(200):
        client = 'Client' + str(random.randint(1, 5))
        material_document_number = random.randint(100000, 999999)
        material_document_year = datetime.now().year
        line_item = random.randint(1, 10)
        material_number = random.randint(1, num_materials)
        plant = 'Plant' + str(random.randint(1, 5))
        storage_location = 'Storage' + str(random.randint(1, 10))
        vendors_account_number = random.randint(1, num_vendors)
        customer_number = random.randint(1, num_customers)
        movement_type = random.choice(['Goods Receipt', 'Goods Issue'])
        receiving_plant = 'Plant' + str(random.randint(1, 5))
        quantity = random.randint(1, 100)
        posting_date_in_the_document = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        material_documents.append((client, material_document_number, material_document_year, line_item,
                                   material_number, plant, storage_location, vendors_account_number,
                                   customer_number, movement_type, receiving_plant, quantity,
                                   posting_date_in_the_document))

    cursor.executemany('''
        INSERT INTO MaterialDocuments (client, material_document_number, material_document_year, line_item,
                                       material_number, plant, storage_location, vendors_account_number,
                                       customer_number, movement_type, receiving_plant, quantity,
                                       posting_date_in_the_document)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', material_documents)

    conn.commit()

    # Generate Material Stocks
    material_stocks = []
    for material in materials:
        material_number = material[0]
        plant = 'Plant' + str(random.randint(1, 5))
        storage_location = 'Storage' + str(random.randint(1, 10))
        client = 'Client' + str(random.randint(1, 5))
        stock_in_quality_inspection = round(random.uniform(0, 100), 2)
        stock_in_transfer = round(random.uniform(0, 100), 2)
        stock_in_posting = round(random.uniform(0, 100), 2)
        stock_of_material_provided_to_vendor = round(random.uniform(0, 100), 2)
        blocked_stock = round(random.uniform(0, 50), 2)
        returns_stock = round(random.uniform(0, 50), 2)
        material_stocks.append((client, material_number, plant, storage_location,
                                stock_in_quality_inspection, stock_in_transfer, stock_in_posting,
                                stock_of_material_provided_to_vendor, blocked_stock, returns_stock))

    cursor.executemany('''
        INSERT INTO MaterialStocks (client, material_number, plant, storage_location,
                                    stock_in_quality_inspection, stock_in_transfer, stock_in_posting,
                                    stock_of_material_provided_to_vendor, blocked_stock, returns_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', material_stocks)

    conn.commit()

    # Generate Order Suggestions
    order_suggestions = []
    num_order_suggestions = 100
    for i in range(1, num_order_suggestions + 1):
        order_number = i
        order_position = 1  # Assuming one position per order for simplicity
        article_number = random.randint(1, num_materials)
        order_quantity = random.randint(1, 100)
        date = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        order_date = date
        delivery_date = order_date + timedelta(days=random.randint(1, 30))
        plant = 'Plant' + str(random.randint(1, 5))
        order_suggestions.append((order_number, order_position, article_number,
                                  order_quantity, date, order_date, delivery_date, plant))

    cursor.executemany('''
        INSERT INTO OrderSuggestions (order_number, order_position, article_number,
                                      order_quantity, date, order_date, delivery_date, plant)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', order_suggestions)

    conn.commit()

    # Generate Purchase Requisitions
    purchase_requisitions = []
    num_purchase_requisitions = 150
    for i in range(1, num_purchase_requisitions + 1):
        client = 'Client' + str(random.randint(1, 5))
        purchase_document_number = random.randint(1, num_purchase_orders)
        item_number_of_purchasing_document = random.randint(1, 5)
        purchase_requisition_number = i
        purchase_requisition_item = random.randint(1, 5)
        purchase_requisition_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        document_type = random.choice(['TypeA', 'TypeB', 'TypeC'])
        purchasing_document_category = random.choice(['Standard', 'Subcontracting', 'Consignment'])
        planned_delivery_time = random.randint(1, 30)
        latest_possible_goods_receipt = purchase_requisition_date + timedelta(days=planned_delivery_time)
        quantity = random.randint(1, 100)
        unit_of_measure = 'PCS'
        purchase_requisitions.append((client, purchase_document_number, item_number_of_purchasing_document,
                                      purchase_requisition_number, purchase_requisition_item,
                                      purchase_requisition_date, document_type, purchasing_document_category,
                                      planned_delivery_time, latest_possible_goods_receipt,
                                      quantity, unit_of_measure))

    cursor.executemany('''
        INSERT INTO PurchaseRequisitions (client, purchase_document_number, item_number_of_purchasing_document,
                                          purchase_requisition_number, purchase_requisition_item,
                                          purchase_requisition_date, document_type, purchasing_document_category,
                                          planned_delivery_time, latest_possible_goods_receipt,
                                          quantity, unit_of_measure)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', purchase_requisitions)

    conn.commit()

    # Generate Sales Document Flows
    sales_document_flows = []
    for _ in range(200):
        client = 'Client' + str(random.randint(1, 5))
        sales_document = random.randint(1, num_sales_orders)
        sales_document_item = random.randint(1, 5)
        subsequent_sales_document = random.randint(1, num_sales_orders)
        subsequent_sales_document_item = random.randint(1, 5)
        document_category_of_subsequent_document = random.choice(['Delivery', 'Invoice', 'Credit Memo'])
        document_category_of_preceding_document = random.choice(['Order', 'Quotation', 'Contract'])
        document_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
        sales_document_flows.append((client, sales_document, sales_document_item,
                                     subsequent_sales_document, subsequent_sales_document_item,
                                     document_category_of_subsequent_document,
                                     document_category_of_preceding_document, document_date))

    cursor.executemany('''
        INSERT INTO SalesDocumentFlows (client, sales_document, sales_document_item,
                                        subsequent_sales_document, subsequent_sales_document_item,
                                        document_category_of_subsequent_document,
                                        document_category_of_preceding_document, document_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', sales_document_flows)

    conn.commit()

def main():
    conn = sqlite3.connect('inventory_management.db')
    create_tables(conn)
    populate_tables(conn)
    conn.close()
    print("Database 'inventory_management.db' created and populated with simulated data.")

if __name__ == '__main__':
    main()
