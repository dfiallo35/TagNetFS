from fastapi.testclient import TestClient

from database.main import app

client = TestClient(app)


# test add
def test_add():
    data = {
        "file_list": [
            {"name": "file1"},
            {"name": "file2"},
            {"name": "file3"}
        ],
        "tag_list": [
            {"name": "tag1"},
            {"name": "tag2"},
        ]
    }
    response = client.post('/add', json=data)
    
    assert response.status_code == 200
    assert response.json() == ["file1", "file2", "file3"]


# test list
def test_list():
    data = [
        "tag1"
    ]
    response = client.get('/list', params=data)
    
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'name': 'file1'}
    ]