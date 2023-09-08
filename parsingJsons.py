import json

def getCountiesIreland():
    with open("resources/NorthernIreland.txt", "r") as f:
        counties: list = f.read().splitlines()
    f.close()
    return counties

counties = getCountiesIreland()

for county in counties:
    f = open('results/' + county + '.json')
    data = json.load(f)
    for key in data.keys():
        with open("NorthernIrelandHotels.txt", "a") as text_file:
            text_file.write(data.get(key).get('name') + " ," + data.get(key).get('location') + "\n")
        print(data.get(key).get('name'))

    f.close()
