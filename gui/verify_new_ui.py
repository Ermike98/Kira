"""
verify_new_ui.py
----------------
Manual test harness to launch the Kira GUI with realistic mock data.
Uses the proper KProject API (process_event + cache_data) to populate state.
"""

import sys
import os
import datetime
import time
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication

from kproject.kproject import KProject
from kproject.kpersistence_manager import KPersistenceManager
from kproject.kevent import KEvent, KEventTypes
from kira import KData, KLiteral, KLiteralType
from gui.qt_project import QTProject
from gui.main_window import run_gui
from kira.knodes.kfunction import kfunction
from kira.library.node_library import KLibrary


def setup_demo_project():
    """Initializes a KProject with mock data and variables."""
    # Create a project with an in-memory database
    pm = KPersistenceManager(None)
    project = QTProject(KProject(pm))

    # --- Register a Slow Function for testing reactivity ---
    test_lib = KLibrary("TestLib")

    @kfunction(inputs=["seconds"], outputs=["result"], name="wait")
    def slow_wait(val):
        # Extract value if it's a KLiteral/KDataValue, otherwise use as is
        seconds = getattr(val, "value", val)
        time.sleep(3)
        return [KLiteral(f"Waited {seconds}s", KLiteralType.STRING)]
    
    test_lib.register(slow_wait)
    test_lib.eval(project.kproject.context)

    # ------------------------------------------------------------------ #
    # 0. Imports for rich mock data                                        #
    # ------------------------------------------------------------------ #
    from kira.kdata.ktable import KTable
    from kira.kdata.karray import KArray

    # ------------------------------------------------------------------ #
    # 1. Static data (KData / Catalogs)                                   #
    # ------------------------------------------------------------------ #

    # KTable — Sales data as a real DataFrame
    sales_df = pd.DataFrame({
        "Region":   ["North", "South", "East", "West", "Central"] * 20,
        "Quarter":  ["Q1", "Q2", "Q3", "Q4"] * 25,
        "Revenue":  [round(v, 2) for v in np.random.uniform(10_000, 500_000, 100)],
        "Units":    np.random.randint(50, 5000, 100).tolist(),
        "Margin_%": [round(v, 1) for v in np.random.uniform(5, 45, 100)],
    })
    sales_kdata = KData("Sales_Table", KTable(sales_df))
    pm.cache_data(sales_kdata)
    project.process_event(KEventTypes.AddData, "Sales_Table")

    # KArray — Customer IDs as a 1-D numpy array
    customer_arr = KArray(np.arange(1, 51, dtype=np.int64))
    customer_kdata = KData("Customer_Data", customer_arr)
    pm.cache_data(customer_kdata)
    project.process_event(KEventTypes.AddData, "Customer_Data")

    # KLiteral — Product catalog label
    catalog_kdata = KData("Product_Catalog", KLiteral("Electronics & Accessories", KLiteralType.STRING))
    pm.cache_data(catalog_kdata)
    project.process_event(KEventTypes.AddData, "Product_Catalog")

    # Add more static data for icon testing
    pm.cache_data(KData("Active_Flag", KLiteral(True, KLiteralType.BOOLEAN)))
    project.process_event(KEventTypes.AddData, "Active_Flag")

    pm.cache_data(KData("Launch_Date", KLiteral(datetime.date(2026, 3, 15), KLiteralType.DATE)))
    project.process_event(KEventTypes.AddData, "Launch_Date")

    pm.cache_data(KData("Version_Num", KLiteral(1.2, KLiteralType.NUMBER)))
    project.process_event(KEventTypes.AddData, "Version_Num")

    # ------------------------------------------------------------------ #
    # 2. Variables (Kira expressions)                                     #
    # ------------------------------------------------------------------ #
    variables = {
        "revenue_total": "revenue_total = 1250000",
        "order_avg":     "order_avg = 348",
        "count_customers": "count_customers = 3594",
        "slow_var":      "slow_var = wait(3)",
    }
    for name, expr in variables.items():
        project.process_event(KEventTypes.AddVariable, name, expr)

    # 3. Tables with long text for testing stretch logic
    long_text = [
        ["The quick brown fox jumps over the lazy dog repeatedly and with great enthusiasm.", "Some other long text that should definitely trigger the 500px threshold if we let it."],
        ["Short text.", "A medium-sized sentence that might exactly hit the stretch logic limits."],
        ["Another very long piece of data designed to test how the table handles columns that are extremely wide based on content alone.", "Final column test."]
    ]
    df_long = pd.DataFrame(long_text, columns=["Extremely_Long_Column_A", "Long_Description_B"])
    pm.cache_data(KData("long_text_table", KTable(df_long)))
    project.process_event(KEventTypes.AddData, "long_text_table")

    # 4. Long text literal
    long_desc = (
        "This is a very long descriptive text intended to test the literal visualization limits. "
        "It contains multiple sentences that should ideally occupy a single line if word wrap is disabled, "
        "checking how the GUI handles overflow or extreme width in the DataView cards."
    )
    pm.cache_data(KData("long_text_literal", KLiteral(long_desc, KLiteralType.STRING)))
    project.process_event(KEventTypes.AddData, "long_text_literal")

    # ------------------------------------------------------------------ #
    # 3. Workflows (Kira DSL)                                             #
    # ------------------------------------------------------------------ #
    workflows = {
        "Clean_Data": (
            "workflow Clean_Data(total_sales) -> result:\n"
            "result = total_sales\n"
            "return result"
        ),
        "Process_Sales": (
            "workflow Process_Sales(table, tax_rate) -> final_table:\n"
            "final_table = table\n"
            "return final_table"
        )
    }
    for name, body in workflows.items():
        project.process_event(KEventTypes.AddWorkflow, name, body)

    return project


if __name__ == "__main__":
    # Setup project
    project = setup_demo_project()
    
    # Run GUI
    app, window = run_gui(project)
    sys.exit(app.exec())
