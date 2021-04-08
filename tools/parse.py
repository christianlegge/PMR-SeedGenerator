import re

from enums import Enums, enum_int


def get_debault_db():
    # Get general data
    db = {}
    with open("../globals/patch/Database.patch", "r") as file:
        db_found = False
        while not db_found:
            if match := re.match(r"#new:Data\s*\$DefaultDatabase", next(file)):
                db_found = True
        for line in file:
            if line.startswith("}"):
                break
            if match := re.match(r"\s*.DBKey:(\S*):(\S*)\s*(\S*)", line):
                table = match.group(1)
                attribute = match.group(2)
                value = match.group(3)
                enum_type = None

                if value == ".True":
                    value = True
                elif value == ".False":
                    value = False
                elif value.endswith("`"): # Decimal
                    value = int(value[:-1])
                else:
                    try:
                        value = int(value, 16) # Hexadecimal
                    except:
                        value,enum_type = enum_int(value) # Convert enum to number

                if table not in db:
                    db[table] = {}
                db[table][attribute] = {
                    "value": value,
                    "enum_type": enum_type,
                    "attribute": attribute,
                    "table": table,
                }
    # Get entrance data
    db["Entrance"] = {}
    with open("../globals/patch/RandomEntrances.patch", "r") as file:
        for line in file:
            if match := re.match(r"#export\s*.DBKey:Entrance:(\S*):(\S*)\s*(\S*)", line):
                map_name = match.group(1)
                map_exit = int(match.group(2), 16)
                key = match.group(3)
                byte_id = int(key[0:2], 16)
                area_id = int(key[2:4], 16)
                map_id =  int(key[4:6], 16)
                entry_id =  int(key[6:8], 16)

                if map_name not in db["Entrance"]:
                    db["Entrance"][map_name] = {}
                db["Entrance"][map_name][map_exit] = {
                    "byte_id": byte_id,
                    "area": area_id,
                    "map": map_id,
                    "entry": entry_id,
                }
    return db
            
def get_table_info():
    # Defaults
    table_info = {
        "magic_value": 0x504D4442,
        "header_size": 0x20,
        "num_entries": 0,
        "seed": 0xDEADBEEF,
        "address": 0x1D00000,
    }
    with open("../globals/patch/Database.patch", "r") as file:
        for line in file:
            if match := re.match(r"#define\s*.Table:RomOffset\s*(\S*)", line):
               table_info["address"] = int(match.group(1), 16)
            elif match := re.match(r"#define\s*.Table:Header:MagicValue\s*(\S*)", line):
                table_info["magic_value"] = int(match.group(1), 16)
    return table_info

def create_db(default_db):
    db = {}
    with open("../globals/patch/DatabaseKeys.patch", "r") as file:
        db = {}
        for line in file:
            if match := re.match(r"#export\s*.DBKey:(\S*):(\S*)\s*(\S*)", line):
                table = match.group(1)
                attribute = match.group(2)
                key = int(match.group(3), 16)
                if table not in db:
                    db[table] = {}

                if data := default_db.get(table, {}).get(attribute):
                    default_value = data["value"]
                    default_type = data["enum_type"]
                    db[table][attribute] = {
                        "key": key,
                        "value": default_value,
                        "attribute": attribute,
                        "table": table,
                        "enum_type": {
                            0xAF: "Option",
                            0xA1: "Item",
                            0xA2: "Actor",
                            0xA3: "Entrance",
                            0xA4: "Palette",
                        }.get((key & 0xFF000000) >> 24)
                    }

    db["Entrance"] = {}
    for map_name,entrance_data in default_db["Entrance"].items():
        db["Entrance"][map_name] = {}
        for entrance,data in entrance_data.items():
            db_key = (data["byte_id"] << 24) | (data["area"] << 16) | (data["map"] << 8) | data["entry"]
            db["Entrance"][map_name][entrance] = {
                "key": db_key,
                "value": db_key & 0x00FFFFFF,
                "map_name": map_name,
                "entrance": entrance,
                "enum_type": {
                    0xAF: "Option",
                    0xA1: "Item",
                    0xA2: "Actor",
                    0xA3: "Entrance",
                    0xA4: "Palette",
                }.get((db_key & 0xFF000000) >> 24)
            }

    return db