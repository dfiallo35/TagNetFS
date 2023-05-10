

def add(file_list: list[str], tag_list: list[str]):
    '''
    Copy the files to the system and assign them the tags
    '''
    ...


def delete(tag_query: list[str]):
    '''
    Delete all the files that match the tag query
    '''
    ...


def qlist(tag_query: list[str]):
    '''
    List the name and the tags of every file that match the tag query
    '''
    ...


def add_tags(tag_query: list[str], tag_list: list[str]):
    '''
    Add the tags from the tag list to the files that match the tag query
    '''
    ...


def delete_tags(tag_query: list[str], tag_list: list[str]):
    '''
    Delete the tags from the tag list to the files that match the tag query
    '''
    ...