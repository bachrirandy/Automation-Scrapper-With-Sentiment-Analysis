from bs4 import BeautifulSoup
import requests

response = requests.get('https://example.com')
soup = BeautifulSoup(response.text, 'html.parser')

for item in soup.select('.product'):
    nama = item.find('h3').text.strip()
    harga = item.find('h4').text.strip()
    
    