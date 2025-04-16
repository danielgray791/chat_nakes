import asyncio
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

from typing import Literal, Optional

from pymongo.server_api import ServerApi
from pymongo import MongoClient

DB_NAME = "telegram_chat"

ColumnNameLiteral = Literal[ 
   "semarankes_chat",
   "ip_list"
]

URI = "mongodb+srv://lilokopa1:lilokopa009@cluster0.tlefh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

class MongoDB: 
    def __init__(
            self,  
            db_name: str = DB_NAME, 
            collection_name: Optional[ColumnNameLiteral] = "semarankes_chat",
            uri: str = ""
        ): 
        self.client = MongoClient(URI, server_api=ServerApi("1"))
        self.db = self.client.get_database(db_name)
        self.collection = self.db.get_collection(collection_name)
    
    async def get(self, key: str): 
        _id, data = None, None
        query = { key: { "$exists": True } }

        find_result = await asyncio.to_thread(self.collection.find_one, query)
        if not find_result: 
            return _id, data

        _id, data, = find_result.values()
        return _id, data

    async def set(self, data: dict) -> bool: 
        key = str(data["id"])
        _id, existing_data = await self.get(key)

        if existing_data is None: 
            insert_data = { key : data}
            result = await asyncio.to_thread(self.collection.insert_one, insert_data)
            return result.acknowledged
        
        query = [
            {'_id': _id},
            {'$set': {key: data}}
        ]

        result = await asyncio.to_thread(self.collection.update_one, *query)
        return result.modified_count > 0

    async def set_field(
        self,
        key: str, 
        target_field: str, 
        value: any
    ) -> bool: 
        _id, existing_data = await self.get(key)
        if not _id or not existing_data: 
            return False
        
        query = { "_id": _id }

        new_values = { "$set": { ".".join([key, target_field]): value }}

        result = await asyncio.to_thread(self.collection.update_one, query, new_values)
        return result.modified_count > 0
    
    async def clear(self, col_name: Optional[ColumnNameLiteral]): 
        collection = self.collection if not col_name else self.db.get_collection(col_name)
        result = await asyncio.to_thread(collection.delete_many, {})
        return result.acknowledged
    
    async def change_collection(self, name: Optional[ColumnNameLiteral]): 
        self.collection = self.db.get_collection(name)

async def main(): 
    return
    # db = MongoDB()
    # await db.clear()
    # find_result = await asyncio.to_thread(db.collection.find)
    # for result in find_result: 
    #     _id, chat_data = result.values()
    #     if "Nabhan" in chat_data["name"]: 
    #         print(chat_data)
    #         break
    # print(list(find_result))
    # await db.clear()
    
    # query = { "2027129203": {} }
    # data =  collection.find_one(query)
    # data = "5732923292": {
    #     'name': 'My Time Is Up', 
    #     'chat_config': {
    #         'model': 'gpt-4o'
    #     }, 
    #     'menu': '', 
    #     'action': ''
    # }

    # data = {
    #     "5732923292": {
    #         "id": "5732923292",
    #         "name": "My Time Is Up", 
    #         "chat_config": {
    #             "model": "gpt-4o"
    #         }, 
    #         "menu": "", 
    #         "action": ""
    #     }
    # }
    # add_result = await database.add_user(user_data=data)
    # chat_config = {
    #     "model": "gpt-4l"
    # }
    # update_value= ""
    # await database.update_user(user_id="5732923292", target_field="menu", value=update_value)
    # print(add_result)
    # print(await database.user_exists(key="57329232921"))

if __name__ == "__main__": 
    asyncio.run(main())
