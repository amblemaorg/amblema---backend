import requests
import json

pecaId = "68daf9b498d6455346b6f554"
data = {
    "sections": [
        {
            "id": "68e3c53f98d6455346b7101d",
            "groupedWith": "TESTING123"
        }
    ]
}

response = requests.patch(f'http://localhost:5000/pecaprojects/yearbook/sectiongrouping/{pecaId}', json=data)
print(response.status_code)
print(response.text)

# And verify it saved!
response = requests.get(f'http://localhost:5000/pecaprojects/{pecaId}')
data = response.json()
for section in data['school']['sections']:
    if section['id'] == "68e3c53f98d6455346b7101d":
        print("After Fetch Grp:", section.get('groupedWith'))
