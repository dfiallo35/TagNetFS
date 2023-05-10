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
    assert response.json() == {"message": "success"}



# test list
def test_list():
    data = {
        "tag_query": [
            "tag1"
        ]
    }
    response = client.get('/files/', params=data)
    
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'name': 'file1', 'tags':[{'id':1, 'name':'tag1'}, {'id':2, 'name':'tag2'}]},
        {'id': 2, 'name': 'file2', 'tags':[{'id':1, 'name':'tag1'}, {'id':2, 'name':'tag2'}]},
        {'id': 3, 'name': 'file3', 'tags':[{'id':1, 'name':'tag1'}, {'id':2, 'name':'tag2'}]}
    ]


# test add_tags
def test_add_tags():
    data = {
        "tag_query": [
            "tag1"
        ],
        "tag_list": [
            "tag3"
        ]
    }
    response = client.post('/add_tags', json=data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


# # test delete_tags
def test_delete_tags():
    data = {
        "tag_query": [
            "tag1"
        ],
        "tag_list": [
            "tag3"
        ]
    }
    response = client.delete('/delete_tags', params=data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


# # test delete
def test_delete():
    data = {
        "tag_query": [
            "tag1"
        ]
    }
    response = client.delete('/delete', params=data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
