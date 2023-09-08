
import json
from pathlib import Path

def getCountiesIreland():
    with open("resources/Ireland.txt", "r") as f:
        counties: list = f.read().splitlines()
    f.close()
    return counties

result_search = {}

out = Path(__file__).parent / "ireland"
out.mkdir(exist_ok=True)
counties = getCountiesIreland()
for county in counties:
    out.joinpath(county + ".json").write_text(json.dumps(result_search, indent=2, ensure_ascii=False))