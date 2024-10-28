import http.client
import urllib.parse

# Define the server and endpoint
server = "example.com"
endpoint = "/api/data"

# Prepare the data for the POST request
data = {
    "key1": "value1",
    "key2": "value2"
}
encoded_data = urllib.parse.urlencode(data)  # Encode the data
headers = {
    "Content-type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

# Create an HTTP connection to the server
conn = http.client.HTTPConnection(server)

# Send the POST request
conn.request("POST", endpoint, body=encoded_data, headers=headers)

# Get the response
response = conn.getresponse()
print("Status:", response.status)
print("Reason:", response.reason)
print("Response data:", response.read().decode())

# Close the connection
conn.close()