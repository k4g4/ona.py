from pymongo import MongoClient, ReturnDocument
from cachetools import LRUCache
from contextlib import contextmanager


class OnaDocument(dict):
    '''This class represents a generic MongoDB document.'''

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class OnaDB:
    '''Database interactions are handled here.'''

    def __init__(self, ona, collection):
        self.ona = ona
        self.client = MongoClient(self.ona.secrets.host, self.ona.secrets.port)
        self.collection = self.client.ona[collection]
        self.doc_cache = LRUCache(self.ona.config.max_db_cache)

    def get_doc(self, _id):
        if _id in self.doc_cache:
            return self.doc_cache[_id]
        doc = OnaDocument(self.collection.find_one_and_update({"_id": _id}, {"$setOnInsert": {"money": 0}},
                                                              upsert=True, return_document=ReturnDocument.AFTER))
        self.doc_cache[_id] = doc
        return doc

    def update_doc(self, doc):  # This method should only ever be called by doc_context
        if not self.collection.replace_one({"_id": doc["_id"]}, doc).matched_count:
            self.collection.insert_one({"_id": doc["_id"]})

    @contextmanager
    def doc_context(self, _id):
        '''Incorporate get_doc and update_doc as a single contextmanager.'''
        doc = self.get_doc(_id)
        yield doc
        self.update_doc(doc)
