import sqlite3
import pandas as pd
import numpy as np

query = """
WITH MaterialsPlants AS (
    -- List all unique combinations of material and plant
    SELECT DISTINCT material_number, plant FROM PurchaseOrderItems
    UNION
    SELECT DISTINCT material_number, plant FROM GoodsReceiptsAndIssues
    UNION
    SELECT DISTINCT material_number, plant FROM SalesOrderItems
    UNION
    SELECT DISTINCT article_number AS material_number, plant FROM OrderSuggestions
),

DailyDemand AS (
    -- Calculate daily demand for each material and plant
    SELECT
        gri.material_number AS material_number,
        gri.plant AS plant,
        DATE(gri.date_of_the_posting_in_the_document) AS demand_date,
        SUM(gri.quantity) AS daily_quantity
    FROM
        GoodsReceiptsAndIssues gri
    WHERE
        gri.movement_type = 'Goods Issue'
        AND gri.date_of_the_posting_in_the_document >= DATE('now', '-1 year')
    GROUP BY
        gri.material_number,
        gri.plant,
        DATE(gri.date_of_the_posting_in_the_document)
),

AnnualDemand AS (
    -- Aggregate daily demand to compute annual demand and statistics
    SELECT
        mp.material_number,
        mp.plant,
        SUM(dd.daily_quantity) AS annual_demand,
        AVG(dd.daily_quantity) AS average_daily_demand,
        COUNT(DISTINCT dd.demand_date) AS days_with_demand,
        -- Calculate variance and standard deviation
        (AVG(dd.daily_quantity * dd.daily_quantity) - AVG(dd.daily_quantity) * AVG(dd.daily_quantity)) AS variance_daily_demand,
        SQRT(AVG(dd.daily_quantity * dd.daily_quantity) - AVG(dd.daily_quantity) * AVG(dd.daily_quantity)) AS stddev_daily_demand
    FROM
        MaterialsPlants mp
    LEFT JOIN
        DailyDemand dd ON mp.material_number = dd.material_number AND mp.plant = dd.plant
    GROUP BY
        mp.material_number,
        mp.plant
),

LeadTimes AS (
    -- Calculate average lead time, excluding negative lead times
    SELECT
        t.material_number,
        t.plant,
        AVG(t.LeadTimeDays) AS average_lead_time
    FROM
        (
            SELECT
                poi.material_number,
                poi.plant,
                (JULIANDAY(gri.date_of_the_posting_in_the_document) - JULIANDAY(pod.purchase_order_date)) AS LeadTimeDays
            FROM
                PurchaseOrderItems poi
            JOIN PurchaseOrderDocuments pod ON poi.purchase_order_number = pod.purchase_document_number
            JOIN GoodsReceiptsAndIssues gri ON poi.purchase_order_number = gri.purchase_document_number
                AND poi.purchase_order_item_number = gri.line_item_in_purchase_document
            WHERE
                gri.movement_type = 'Goods Receipt'
                AND pod.purchase_order_date IS NOT NULL
                AND gri.date_of_the_posting_in_the_document IS NOT NULL
                AND gri.date_of_the_posting_in_the_document >= DATE('now', '-1 year')
        ) t
    WHERE
        t.LeadTimeDays >= 0  -- Exclude negative lead times
    GROUP BY
        t.material_number,
        t.plant
),

Calculations AS (
    SELECT
        mp.material_number,
        mp.plant,
        -- Handle missing annual demand and average daily demand
        COALESCE(ad.annual_demand, 0) AS annual_demand,
        COALESCE(NULLIF(ad.average_daily_demand, 0), 1.0) AS average_daily_demand,
        -- Handle missing or zero standard deviation
        COALESCE(NULLIF(ad.stddev_daily_demand, 0), COALESCE(ad.average_daily_demand, 1.0) * 0.1) AS stddev_daily_demand,
        -- Handle missing or negative lead time
        COALESCE(NULLIF(lt.average_lead_time, 0), 7.0) AS average_lead_time,
        -- Constants
        100.0 AS fixed_order_cost,  -- S
        10.0 AS holding_cost_per_unit_per_year,  -- H
        1.645 AS z_score  -- z (for 95% service level)
    FROM
        MaterialsPlants mp
    LEFT JOIN
        AnnualDemand ad ON mp.material_number = ad.material_number AND mp.plant = ad.plant
    LEFT JOIN
        LeadTimes lt ON mp.material_number = lt.material_number AND mp.plant = lt.plant
)

SELECT
    c.material_number AS "Material Number",
    c.plant AS "Plant",
    c.annual_demand AS "Annual Demand (D_m)",
    c.average_daily_demand AS "Average Daily Demand (d_m)",
    c.stddev_daily_demand AS "Std Dev of Daily Demand (σ_m)",
    c.average_lead_time AS "Average Lead Time (l_m)",
    -- Calculate EOQ, handling cases where annual demand is zero
    ROUND(CASE WHEN c.annual_demand > 0 THEN SQRT((2 * c.annual_demand * c.fixed_order_cost) / c.holding_cost_per_unit_per_year) ELSE 0 END, 2) AS "EOQ",
    -- Calculate Safety Stock (SS)
    ROUND(c.z_score * c.stddev_daily_demand * SQRT(c.average_lead_time), 2) AS "Safety Stock (SS)",
    -- Calculate Reorder Point (ROP)
    ROUND((c.average_daily_demand * c.average_lead_time) + (c.z_score * c.stddev_daily_demand * SQRT(c.average_lead_time)), 2) AS "Reorder Point (ROP)"
FROM
    Calculations c
ORDER BY
    c.material_number,
    c.plant;
"""


def calculate_inventory_parameters(db_path):
    conn = sqlite3.connect(db_path)
    results = pd.read_sql_query(query, conn)
    conn.close()
    return results


def fix_type_column(x, col):
    if x is None or pd.isna(x):
        return x
    elif x.startswith("["):
        return eval(x)
    else:
        return [x]


if __name__ == '__main__':
    df1 = calculate_inventory_parameters('inventory_management.db')
    df2 = pd.read_csv("ocel_inventory_management.csv")

    df2["ocel:type:MAT"] = df2["ocel:type:MAT"].apply(lambda x: x.split('\'')[1])
    df2["ocel:type:PLA"] = df2["ocel:type:PLA"].apply(lambda x: x.split('\'')[1])

    df1["Material Number"] = "MAT-"+df1["Material Number"].astype("string")

    # Step 1: Merge the DataFrames
    df1_renamed = df1.rename(columns={
        'Material Number': 'ocel:type:MAT',
        'Plant': 'ocel:type:PLA'
    })

    df_merged = pd.merge(df2, df1_renamed, on=['ocel:type:MAT', 'ocel:type:PLA'], how='left')

    # Step 2: Compute Overstock (OS)
    df_merged['OS'] = df_merged['Safety Stock (SS)'] + df_merged['EOQ']

    df_merged.dropna(subset=["OS", "EOQ", "Safety Stock (SS)", "Stock Before", "Stock After"], inplace=True)
    # Step 3: Apply Transformation Rules


    def get_statuss(row):
        stock_after = row['Stock After']

        SS = row['Safety Stock (SS)']
        OS = row['OS']

        if stock_after < SS:
            return "Understock"
        elif stock_after > OS:
            return "Overstock"
        else:
            return "Normal"

    def status_change_happened(row):
        activity = row["ocel:activity"]
        stock_before = row['Stock Before']
        stock_after = row['Stock After']
        cumcount = row["CUMCOUNT"]
        invcumcount = row["INVCUMCOUNT"]

        SS = row['Safety Stock (SS)']
        OS = row['OS']

        ret_label = None

        if cumcount == 0:
            if stock_after < SS:
                ret_label = "START UNDERSTOCK"
            elif stock_after >= OS:
                ret_label = "START OVERSTOCK"
            else:
                ret_label = "START NORMAL"
        else:
            label_before = "UNDERSTOCK" if stock_before < SS else "OVERSTOCK" if stock_before >= OS else "NORMAL"
            label_after = "UNDERSTOCK" if stock_after < SS else "OVERSTOCK" if stock_after >= OS else "NORMAL"

            if label_before != label_after:
                ret_label = "ST CHANGE "+label_before+" to "+label_after

        return ret_label


    def status_change_happened2(row):
        activity = row["ocel:activity"]
        stock_before = row['Stock Before']
        stock_after = row['Stock After']
        cumcount = row["CUMCOUNT"]
        invcumcount = row["INVCUMCOUNT"]

        SS = row['Safety Stock (SS)']
        OS = row['OS']

        ret_label = None

        if invcumcount == 0:
            if stock_after < SS:
                ret_label = "END UNDERSTOCK"
            elif stock_after >= OS:
                ret_label = "END OVERSTOCK"
            else:
                ret_label = "END NORMAL"

        return ret_label



    df_merged["CUMCOUNT"] = df_merged.groupby("ocel:type:MAT_PLA").cumcount()
    df_merged['INVCUMCOUNT'] = (
        df_merged.iloc[::-1]
        .groupby('ocel:type:MAT_PLA')
        .cumcount()
        .iloc[::-1]
    )

    df_merged["Current Status"]  = df_merged.apply(
        lambda row: get_statuss(row),
        axis=1
    )
    df_merged['ocel:activity'] = df_merged["ocel:activity"] + " (" + df_merged["Current Status"] + ")"

    df_merged['Status Change Happened'] = df_merged.apply(lambda row: status_change_happened(row), axis=1)
    df_merged['Status Change Happened2'] = df_merged.apply(lambda row: status_change_happened2(row), axis=1)
    df_merged['Status Change Happened3'] = (
        df_merged.groupby('ocel:type:MAT_PLA')['Current Status']
        .transform(lambda x: np.where(
            x.shift(1) == x,
            np.nan,
            "ST CHANGE " + x.shift(1) + " to " + x
        ))
        .fillna(np.nan)
    )
    df_merged['Status Change Happened4'] = np.where(
        (df_merged['Status Change Happened'].notna()),
        np.nan,
        df_merged['Status Change Happened3']
    )

    if False:
        # Update 'ocel:activity' in df2
        df2_updated = df2.copy()
        df2_updated['ocel:activity'] = df_merged['Transformed Activity']
        df2_updated['Status Change Happened'] = df_merged['Status Change Happened']
    else:
        df2_updated = df_merged

    seconds = df2_updated.index * 10

    # Convert to hh:mm:ss format
    hh = (seconds // 3600).astype(str).str.zfill(2)
    mm = ((seconds % 3600) // 60).astype(str).str.zfill(2)
    ss = (seconds % 60).astype(str).str.zfill(2)
    time_str = hh + ':' + mm + ':' + ss
    df2_updated['ocel:timestamp'] = df2_updated['ocel:timestamp'] + ' ' + time_str
    df2_updated.sort_values(["ocel:timestamp"], inplace=True)

    df2_updated["ocel:timestamp"] = pd.to_datetime(df2_updated["ocel:timestamp"])

    df3 = df2_updated.dropna(subset=["Status Change Happened"])

    df4 = df2_updated.dropna(subset=["Status Change Happened"])
    df4["ocel:activity"] = df4["Status Change Happened"]
    df4["ocel:timestamp"] = df4["ocel:timestamp"] - pd.to_timedelta(1, unit='s')
    df4["ocel:eid"] = df4["ocel:eid"] + "_STARTSC"

    df5 = df2_updated.dropna(subset=["Status Change Happened2"])
    df5["ocel:activity"] = df5["Status Change Happened2"]
    df5["ocel:timestamp"] = df5["ocel:timestamp"] + pd.to_timedelta(1, unit='s')
    df5["ocel:eid"] = df5["ocel:eid"] + "_END"

    df6 = df2_updated.dropna(subset=["Status Change Happened4"])
    df6["ocel:activity"] = df6["Status Change Happened4"]
    df6["ocel:timestamp"] = df6["ocel:timestamp"] - pd.to_timedelta(1, unit='s')
    df6["ocel:eid"] = df6["ocel:eid"] + "_ARTSC"

    df2_updated = pd.concat([df2_updated, df4, df5, df6])
    df2_updated.sort_values(["ocel:type:MAT_PLA", "ocel:timestamp"], inplace=True)

    for col in df2_updated.columns:
        if col.startswith("ocel:type"):
            df2_updated[col] = df2_updated[col].apply(lambda x: fix_type_column(x, col))

    df2_updated.to_csv("post_ocel_inventory_management.csv", index=False)
