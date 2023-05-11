from fastapi.testclient import TestClient

from database.main import app

client = TestClient(app)


# test add
def test_add():
    files = [
        ("file_list", ("file1.txt", open("test/test_files/file1.txt", "rb"), "application/octet-stream")),
        ("file_list", ("file2.txt", open("test/test_files/file2.txt", "rb"), "application/octet-stream")),
        ("file_list", ("file3.txt", open("test/test_files/file3.txt", "rb"), "application/octet-stream"))
    ]
    data = {
        'tag_list':[
            "tag1",
            "tag2"
        ]
    }

    response = client.post('/add', files=files, data=data)
    
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
        {'id': 1, 'name': 'file1.txt', 'tags':[{'id':1, 'name':'tag1'}, {'id':2, 'name':'tag2'}]},
        {'id': 2, 'name': 'file2.txt', 'tags':[{'id':1, 'name':'tag1'}, {'id':2, 'name':'tag2'}]},
        {'id': 3, 'name': 'file3.txt', 'tags':[{'id':1, 'name':'tag1'}, {'id':2, 'name':'tag2'}]}
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


# test delete_tags
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


# test delete
def test_delete():
    data = {
        "tag_query": [
            "tag1"
        ]
    }
    response = client.delete('/delete', params=data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
