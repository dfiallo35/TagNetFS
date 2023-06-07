import Pyro5.api

from app.database.main import *



@Pyro5.api.expose
class Worker():
    def __init__(self):
        ...
    
    def add(self, file_list: List[UploadFile], tag_list: List[str]):
        add(file_list, tag_list)

    def delete(self, tag_query: List[str]):
        delete(tag_query)

    def list(self, tag_query: List[str]):
        qlist(tag_query)
    
    def add_tags(self, tag_query: List[str], tag_list: List[str]):
        add_tags(tag_query, tag_list)
    
    def delete_tags(self, tag_query: List[str], tag_list: List[str]):
        delete_tags(tag_query, tag_list)