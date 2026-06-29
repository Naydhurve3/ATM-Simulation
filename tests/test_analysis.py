import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.data_analysis import DataAnalysis
da = DataAnalysis()
print("Banks:", len(da.get_banks()))
print("Months:", da.get_months())
top = da.top_banks("Total_Txn_Vol", 5)
for b, v in top.items():
    print("  {}: {:,.0f}".format(b, v))
ch = da.channel_breakdown("STATE BANK OF INDIA")
for k, v in ch.items():
    print("  {}: Vol={:,.0f}".format(k, v["Vol"]))
stats = da.get_statistics("Total_Txn_Vol")
for k, v in stats.items():
    print("  {}: {:,.0f}".format(k, v))
print("Test passed!")
