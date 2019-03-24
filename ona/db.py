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

    def __init__(self, host, port, db, collection, template, db_cache_size):
        self.client = MongoClient(host, port)
        self.collection = self.client[db][collection]
        self.template = template
        self.doc_cache = LRUCache(db_cache_size)

    def get_doc(self, snowflake):
        # Default to 0 if the snowflake doesn't exist (i.e. ctx.guild in a PrivateChannel)
        _id = snowflake.id if hasattr(snowflake, "id") else 0
        if _id in self.doc_cache:
            doc = self.doc_cache[_id]
        else:
            doc = OnaDocument(self.collection.find_one_and_update({"_id": _id}, {"$setOnInsert": self.template},
                                                                  upsert=True, return_document=ReturnDocument.AFTER))
            self.doc_cache[_id] = doc
        if not doc.keys() > self.template.keys():   # Basically, "the doc does not have every key in the template"
            [doc.setdefault(key, self.template[key]) for key in self.template]    # Fill up missing keys
            self.update_doc(doc)
        return doc

    def update_doc(self, doc):  # This method should only ever be called by doc_context
        if not self.collection.replace_one({"_id": doc["_id"]}, doc).matched_count:
            self.collection.insert_one({"_id": doc["_id"]})

    @contextmanager
    def doc_context(self, snowflake):
        '''Incorporate get_doc and update_doc as a single contextmanager.'''
        doc = self.get_doc(snowflake)
        yield doc
        self.update_doc(doc)


def setup(ona):
    ona.guild_db = OnaDB(ona.secrets.host, ona.secrets.port, ona.config.db,
                         ona.config.guild_db, ona.guild_doc.to_dict(), ona.config.db_cache_size)
    ona.user_db = OnaDB(ona.secrets.host, ona.secrets.port, ona.config.db,
                        ona.config.user_db, ona.user_doc.to_dict(), ona.config.db_cache_size)
