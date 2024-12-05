import json


async def price_info(file_path):
    try:
        # Open and load the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract values
        price_list = data.get("price_list", {})
        ton_value = data.get("TON", "")
        conversion_rate = data.get("conversion_rate", "")

        # Convert all numeric values in price_list to integers
        price_list = {key: float(value) if isinstance(value, (int, float)) else value for key, value in
                      price_list.items()}

        if str(ton_value).replace('.', '', 1).isdigit():
            ton_value = float(ton_value)

        # Return the extracted values
        return price_list, ton_value, conversion_rate

    except FileNotFoundError:
        return None, None, None
    except json.JSONDecodeError:
        return None, None, None


async def rewrite_stars(new_price_list):
    try:
        # Open the file and load the existing data
        with open('price_info.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Update only the price_list part of the data
        data['price_list'] = new_price_list

        # Write the updated data back to the file
        with open('price_info.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

    except Exception:
        return


async def rewrite_ton(new_ton_price):
    try:
        # Open the file and load the existing data
        with open('price_info.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Update only the price_list part of the data
        data['TON'] = new_ton_price

        # Write the updated data back to the file
        with open('price_info.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except Exception:
        return


async def rewrite_conversion_rate(new_rate):
    try:
        # Open the file and load the existing data
        with open('price_info.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Update only the price_list part of the data
        data['conversion_rate'] = new_rate

        # Write the updated data back to the file
        with open('price_info.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

    except Exception:
        return
