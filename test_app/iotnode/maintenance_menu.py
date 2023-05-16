import csv

class MaintenanceMenu():

    def __init__(self, filename):
        self._filename = filename

    def get_maintenance_links(self) -> dict:
        maintenance_links = {}
        try:
            with open(self._filename) as csvfile:
                data = csv.reader(csvfile)
                for row in data:
                    if row[0] == '#':
                        continue
                    else:
                        maintenance_links[row[1]]=row[4]
                return maintenance_links
        except FileNotFoundError as exec:
            print(exec)