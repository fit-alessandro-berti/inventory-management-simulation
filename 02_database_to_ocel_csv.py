import sqlite3
import pandas as pd
import numpy as np


query = """
WITH StockChanges AS (
    SELECT
        material_number,
        date_of_the_posting_in_the_document AS event_time,
        CASE
            WHEN movement_type = 'Goods Receipt' THEN quantity
            WHEN movement_type = 'Goods Issue' THEN -quantity
            ELSE 0
        END AS quantity_change
    FROM
        GoodsReceiptsAndIssues
),
AllEvents AS (
    -- Create Purchase Suggestion Item
    SELECT
        'Create Purchase Suggestion Item' AS Activity,
        os.date AS Timestamp,
        os.article_number AS "Obj Type MAT",
        os.plant AS "Obj Type PLA",
        NULL AS "Obj Type PO_ITEM",
        NULL AS "Obj Type SO_ITEM",
        NULL AS "Obj Type CUSTOMER",
        NULL AS "Obj Type SUPPLIER",
        0 AS quantity_change
    FROM
        OrderSuggestions os
    WHERE
        os.article_number IS NOT NULL

    UNION ALL

    -- Create Purchase Order Item
    SELECT
        'Create Purchase Order Item' AS Activity,
        pod.purchase_order_date AS Timestamp,
        poi.material_number AS "Obj Type MAT",
        poi.plant AS "Obj Type PLA",
        poi.purchase_order_number || '-' || poi.purchase_order_item_number AS "Obj Type PO_ITEM",
        NULL AS "Obj Type SO_ITEM",
        NULL AS "Obj Type CUSTOMER",
        pod.account_number_of_vendor AS "Obj Type SUPPLIER",
        0 AS quantity_change
    FROM
        PurchaseOrderItems poi
    INNER JOIN PurchaseOrderDocuments pod ON poi.purchase_order_number = pod.purchase_document_number
    WHERE
        poi.material_number IS NOT NULL

    UNION ALL

    -- Goods Receipt
    SELECT
        'Goods Receipt' AS Activity,
        gri.date_of_the_posting_in_the_document AS Timestamp,
        gri.material_number AS "Obj Type MAT",
        gri.plant AS "Obj Type PLA",
        gri.purchase_document_number || '-' || gri.line_item_in_purchase_document AS "Obj Type PO_ITEM",
        NULL AS "Obj Type SO_ITEM",
        NULL AS "Obj Type CUSTOMER",
        pod.account_number_of_vendor AS "Obj Type SUPPLIER",
        gri.quantity AS quantity_change  -- Positive quantity
    FROM
        GoodsReceiptsAndIssues gri
    LEFT JOIN PurchaseOrderDocuments pod ON gri.purchase_document_number = pod.purchase_document_number
    WHERE
        gri.movement_type = 'Goods Receipt' AND gri.material_number IS NOT NULL

    UNION ALL

    -- Create Sales Order Item
    SELECT
        'Create Sales Order Item' AS Activity,
        sod.document_creation_date AS Timestamp,
        soi.material_number AS "Obj Type MAT",
        soi.plant AS "Obj Type PLA",
        NULL AS "Obj Type PO_ITEM",
        soi.sales_document_number || '-' || soi.item_number AS "Obj Type SO_ITEM",
        sod.customer_number AS "Obj Type CUSTOMER",
        NULL AS "Obj Type SUPPLIER",
        0 AS quantity_change
    FROM
        SalesOrderItems soi
    INNER JOIN SalesOrderDocuments sod ON soi.sales_document_number = sod.sales_document_number
    WHERE
        soi.material_number IS NOT NULL

    UNION ALL

    -- Goods Issue
    SELECT
        'Goods Issue' AS Activity,
        gri.date_of_the_posting_in_the_document AS Timestamp,
        gri.material_number AS "Obj Type MAT",
        gri.plant AS "Obj Type PLA",
        NULL AS "Obj Type PO_ITEM",
        NULL AS "Obj Type SO_ITEM",
        gri.reference_document_number AS "Obj Type CUSTOMER",
        NULL AS "Obj Type SUPPLIER",
        -gri.quantity AS quantity_change  -- Negative quantity
    FROM
        GoodsReceiptsAndIssues gri
    WHERE
        gri.movement_type = 'Goods Issue' AND gri.material_number IS NOT NULL
)

SELECT
    Activity,
    Timestamp,
    "Obj Type MAT",
    "Obj Type PLA",
    "Obj Type PO_ITEM",
    "Obj Type SO_ITEM",
    "Obj Type CUSTOMER",
    "Obj Type SUPPLIER",
    SUM(quantity_change) OVER (
        PARTITION BY "Obj Type MAT"
        ORDER BY Timestamp
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS "Stock Before",
    SUM(quantity_change) OVER (
        PARTITION BY "Obj Type MAT"
        ORDER BY Timestamp
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS "Stock After"
FROM
    AllEvents
WHERE
    "Obj Type MAT" IS NOT NULL
ORDER BY
    "Obj Type MAT",
    Timestamp;
"""


def extract_event_log(db_path):
    conn = sqlite3.connect(db_path)
    event_log = pd.read_sql_query(query, conn)
    conn.close()
    return event_log


def fix_type_column(x, col):
    if x is None or pd.isna(x):
        return x
    if type(x) is not str:
        x = str(int(x))
    col = col.split("ocel:type:")[1]
    if "MAT" not in col and "PLA" not in col:
        x = col+"--"+x
    return [x]


if __name__ == '__main__':
    event_log_df = extract_event_log('inventory_management.db')
    event_log_df = event_log_df.rename(columns={"Activity": "ocel:activity", "Timestamp": "ocel:timestamp",
                                                "Obj Type MAT": "ocel:type:MAT", "Obj Type PLA": "ocel:type:PLA", "Obj Type PO_ITEM": "ocel:type:PO_ITEM",
                                                "Obj Type SO_ITEM": "ocel:type:SO_ITEM", "Obj Type CUSTOMER": "ocel:type:CUSTOMER",
                                                "Obj Type SUPPLIER": "ocel:type:SUPPLIER"})
    event_log_df["ocel:type:MAT"] = "MAT-"+event_log_df["ocel:type:MAT"].astype("string")
    event_log_df["ocel:type:PLA"] = event_log_df["ocel:type:PLA"].astype("string")
    event_log_df["ocel:type:MAT_PLA"] = event_log_df["ocel:type:MAT"] + "_" + event_log_df["ocel:type:PLA"]

    event_log_df = event_log_df.dropna(subset=["Stock Before", "Stock After"])

    stock_before_min = event_log_df.groupby("ocel:type:MAT_PLA")["Stock Before"].min().to_dict()
    stock_after_min = event_log_df.groupby("ocel:type:MAT_PLA")["Stock After"].min().to_dict()
    stock_min = {x: min(y, stock_after_min[x]) for x, y in stock_before_min.items()}
    adding_stock = {x: max(0, -y) for x, y in stock_min.items()}
    event_log_df["Stock Before"] = event_log_df["Stock Before"] + event_log_df["ocel:type:MAT_PLA"].map(adding_stock)
    event_log_df["Stock After"] = event_log_df["Stock Before"] + event_log_df["ocel:type:MAT_PLA"].map(adding_stock)

    event_log_df["ocel:eid"] = "e"+event_log_df.index.astype("string")

    for col in event_log_df.columns:
        if col.startswith("ocel:type"):
            event_log_df[col] = event_log_df[col].apply(lambda x: fix_type_column(x, col))

    event_log_df.to_csv("ocel_inventory_management.csv", index=False)
