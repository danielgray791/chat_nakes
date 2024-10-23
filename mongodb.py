import asyncio
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

from pymongo.server_api import ServerApi
from pymongo import MongoClient

DB_NAME = "telegram_chat"
COLL_NAME = "semarankes_chat"
URI = "mongodb+srv://lilokopa1:lilokopa009@cluster0.tlefh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

class MongoDB: 
    def __init__(
            self,  
            db_name: str = "telegram_chat", 
            collection_name: str = "semaran_chat",
            uri: str = ""
        ): 
        self.client = MongoClient(URI, server_api=ServerApi("1"))
        self.db = self.client.get_database(DB_NAME)
        self.collection = self.db.get_collection(COLL_NAME)
    
    async def get(self, user_id: str): 
        _id, user = None, None
        query = { user_id: { "$exists": True } }

        find_result = await asyncio.to_thread(self.collection.find_one, query)
        if not find_result: 
            return _id, user
        
        _id, user_dict, = find_result.values()
        return _id, user_dict

    async def set(self, data: dict) -> bool: 
        user_id = str(data["id"])
        _id, user = await self.get(user_id)

        if user is None: 
            insert_data = { user_id : data}
            result = await asyncio.to_thread(self.collection.insert_one, insert_data)
            return result.acknowledged
        
        query = [
            {'_id': _id},
            {'$set': {user_id: data}}
        ]

        result = await asyncio.to_thread(self.collection.update_one, *query)
        return result.modified_count > 0

    async def set_field(
        self,
        user_id: str, 
        target_field: str, 
        value: any
    ) -> bool: 
        _id, user = await self.get(user_id)
        if not _id or not user: 
            return False
        
        query = { "_id": _id }
        key = f"{user_id}"
        new_values = { "$set": { key: {target_field: value}} }

        result = await asyncio.to_thread(self.collection.update_one, query, new_values)
        return result.modified_count > 0
    
    async def clear(self): 
        result = await asyncio.to_thread(self.collection.delete_many, {})
        return result.acknowledged

async def main(): 
    db = MongoDB()
    await db.clear()
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
