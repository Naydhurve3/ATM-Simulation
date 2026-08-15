import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from atm_cli.app import BankingAnalyticsSuite

if __name__ == "__main__":
    app = BankingAnalyticsSuite()
    app.run()
