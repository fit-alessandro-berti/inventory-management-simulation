# Inventory Management Simulation

This repository contains a small pipeline to generate a synthetic inventory management dataset and produce an object-centric event log (OCEL) from it.  The data can be used for experimentation with process mining or inventory control techniques.

## Overview

1. **01_generate_simulation.py** – creates an SQLite database (`inventory_management.db`) populated with random materials, orders and stock movements.
2. **02_database_to_ocel_csv.py** – queries the database and exports the event log as `ocel_inventory_management.csv`.  Each entry contains involved objects (materials, plants, orders, customers, suppliers) and the stock level before and after the event.
3. **03_ocel_csv_to_ocel.py** – converts the CSV event log into an OCEL XML file (`ocel_inventory_management.xml`).
4. **04_postprocess_activities.py** – enriches the event log with inventory calculations such as EOQ, safety stock and reorder points.  It annotates each event with the resulting stock status and produces a new CSV (`post_ocel_inventory_management.csv`).
5. **05_ocel_csv_to_ocel.py** – converts the post‑processed CSV into an OCEL XML file (`post_ocel_inventory_management.xml`).

Running the scripts sequentially generates the synthetic data and produces event logs suitable for further analysis.

The project is provided under the Apache 2.0 license (see `LICENSE`).
