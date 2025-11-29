from api_client import ApiClient
api = ApiClient()

lines = api.get_lines_raw()

print("First line object:")
print(lines[0])
