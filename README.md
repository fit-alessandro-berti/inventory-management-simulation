## Simulated Inventory Management Database and Object-Centric Event Logs for Process Analysis

**Abstract:**
This repository/dataset provides a suite of Python scripts to generate a simulated relational database for inventory management processes and transform this data into object-centric event logs (OCEL) suitable for advanced process mining analysis. The primary goal is to offer a synthetic yet realistic dataset that facilitates research, development, and application of object-centric process mining techniques in the domain of inventory control and supply chain management. The generated event logs capture common inventory operations, track stock level changes, and are enriched with key inventory management parameters (like EOQ, Safety Stock, Reorder Point) and status-based activity labels (e.g., indicating understock or overstock situations).

**Overview:**
Inventory management is a critical business process characterized by the interaction of various entities such as materials, purchase orders, sales orders, plants, suppliers, and customers. Traditional process mining often struggles to capture these complex interactions. Object-Centric Process Mining (OCPM) offers a more suitable paradigm. This project provides the tools to create and explore such data.

The workflow involves:
1.  **Database Simulation:** Generating a SQLite database with tables for materials, sales orders, purchase orders, goods movements, stock levels, etc., populated with simulated data.
2.  **Initial OCEL Generation:** Extracting data from the SQLite database and structuring it as an object-centric event log (in CSV format). This log includes activities like "Create Purchase Order Item", "Goods Receipt", "Create Sales Order Item", "Goods Issue", and tracks running stock levels for materials.
3.  **OCEL Post-processing and Enrichment:**
    * Calculating standard inventory management metrics such as Economic Order Quantity (EOQ), Safety Stock (SS), and Reorder Point (ROP) for each material-plant combination based on the simulated historical data.
    * Merging these metrics into the event log.
    * Enhancing activity labels to include the current stock status (e.g., "Understock", "Overstock", "Normal") relative to calculated SS and Overstock (OS) levels (where OS = SS + EOQ).
    * Generating new, distinct events to explicitly mark the moments when stock statuses change (e.g., "START UNDERSTOCK", "ST CHANGE NORMAL to OVERSTOCK", "END NORMAL").
4.  **Format Conversion:** Converting the CSV-based OCELs into the standard OCEL XML/OCEL2 format using the `pm4py` library.

**Contents:**

The repository contains the following Python scripts:

* **`01_generate_simulation.py`**:
    * Creates a SQLite database named `inventory_management.db`.
    * Defines and populates tables including: `Materials`, `SalesOrderDocuments`, `SalesOrderItems`, `PurchaseOrderDocuments`, `PurchaseOrderItems`, `PurchaseRequisitions`, `GoodsReceiptsAndIssues`, `MaterialStocks`, `MaterialDocuments`, `SalesDocumentFlows`, and `OrderSuggestions`.
    * Simulates data for a configurable number of materials, customers, sales, purchases, etc., with randomized dates and quantities.

* **`02_database_to_ocel_csv.py`**:
    * Connects to the `inventory_management.db`.
    * Executes a SQL query to extract relevant events and their associated objects for inventory processes.
    * Constructs an initial object-centric event log, saved as `ocel_inventory_management.csv`.
    * Identified object types include: `MAT` (Material), `PLA` (Plant), `PO_ITEM` (Purchase Order Item), `SO_ITEM` (Sales Order Item), `CUSTOMER`, `SUPPLIER`.
    * Calculates "Stock Before" and "Stock After" for each event affecting material stock.
    * Standardizes column names to OCEL conventions (e.g., `ocel:activity`, `ocel:timestamp`, `ocel:type:<OBJECT_TYPE>`).

* **`03_ocel_csv_to_ocel.py`**:
    * Reads `ocel_inventory_management.csv`.
    * Uses `pm4py` to convert the CSV event log into the standard OCEL XML format (`ocel_inventory_management.xml`).

* **`04_postprocess_activities.py`**:
    * Reads data from `inventory_management.db` to calculate inventory parameters:
        * Annual Demand ($D_m$)
        * Average Daily Demand ($d_m$)
        * Standard Deviation of Daily Demand ($\sigma_m$)
        * Average Lead Time ($l_m$)
        * Economic Order Quantity (EOQ): $\sqrt{(2 \cdot D_m \cdot S) / H}$ (where S is fixed order cost, H is holding cost)
        * Safety Stock (SS): $z \cdot \sigma_m \cdot \sqrt{l_m}$ (where z is the z-score for the desired service level)
        * Reorder Point (ROP): $(d_m \cdot l_m) + SS$
    * Merges these calculated parameters with `ocel_inventory_management.csv`.
    * Computes an Overstock level (OS) as $SS + EOQ$.
    * Derives a "Current Status" (Understock, Overstock, Normal) for each event based on "Stock After" relative to SS and OS.
    * Appends this status to the `ocel:activity` label (e.g., "Goods Issue (Understock)").
    * Generates new events for status changes (e.g., "START NORMAL", "ST CHANGE UNDERSTOCK to NORMAL", "END OVERSTOCK") with adjusted timestamps to precisely mark these transitions.
    * Creates a new object type `MAT_PLA` (Material-Plant combination) for easier status tracking.
    * Saves the enriched and transformed log as `post_ocel_inventory_management.csv`.

* **`05_ocel_csv_to_ocel.py`**:
    * Reads the post-processed `post_ocel_inventory_management.csv`.
    * Uses `pm4py` to convert this enriched CSV event log into the standard OCEL XML format (`post_ocel_inventory_management.xml`).

**Generated Dataset Files (if included, or can be generated using the scripts):**

* `inventory_management.db`: The SQLite database containing the simulated raw data.
* `ocel_inventory_management.csv`: The initial OCEL in CSV format.
* `ocel_inventory_management.xml`: The initial OCEL in standard OCEL XML format.
* `post_ocel_inventory_management.csv`: The post-processed and enriched OCEL in CSV format.
* `post_ocel_inventory_management.xml`: The post-processed and enriched OCEL in standard OCEL XML format.

**How to Use:**

1.  Ensure you have Python installed along with the following libraries: `sqlite3` (standard library), `pandas`, `numpy`, `pm4py`.
2.  Run the scripts sequentially in a terminal or command prompt:
    * `python 01_generate_simulation.py` (generates `inventory_management.db`)
    * `python 02_database_to_ocel_csv.py` (generates `ocel_inventory_management.csv` from the database)
    * `python 03_ocel_csv_to_ocel.py` (generates `ocel_inventory_management.xml`)
    * `python 04_postprocess_activities.py` (generates `post_ocel_inventory_management.csv` using the database and the initial CSV OCEL)
    * `python 05_ocel_csv_to_ocel.py` (generates `post_ocel_inventory_management.xml`)

**Potential Applications and Research:**
This dataset and the accompanying scripts can be used for:
* Applying and evaluating object-centric process mining algorithms on inventory management data.
* Analyzing inventory dynamics, such as the causes and effects of understocking or overstocking.
* Discovering and conformance checking process models that involve multiple interacting objects (materials, orders, plants).
* Investigating the impact of different inventory control parameters (EOQ, SS, ROP) on process execution.
* Developing educational materials for teaching OCPM in a supply chain context.
* Serving as a benchmark for new OCEL-based analysis techniques.

**Keywords:**
Object-Centric Event Log, OCEL, Process Mining, Inventory Management, Supply Chain, Simulation, Synthetic Data, SQLite, Python, pandas, pm4py, Economic Order Quantity (EOQ), Safety Stock (SS), Reorder Point (ROP), Stock Status Analysis.
