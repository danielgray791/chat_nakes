import asyncio

from . import pretty_class, MongoDB
from dataclasses import dataclass
from typing import Dict, Optional, List, Any, Union
db = MongoDB(collection_name="ip_list")

@dataclass
class Ip:
    id: str
    ip: str
    type: str
    port: int
    
    def to_dict(self) -> Dict[str, any]: 
        return {
            "id": self.id.replace(".", "_"),
            "ip": self.id,
            "type": self.type,
            "port": int(self.port)
        }

    def __str__(self) -> str: 
        return pretty_class(self)

    @classmethod
    async def get(self, ip: str) -> Optional["Ip"]: 
        _id, ip_data = await db.get(ip)

        if ip_data is None: 
            return None
        
        return cls(
            **ip_data
        )
    
    @classmethod
    async def get_last(cls) -> Optional["Ip"]: 
        result = await asyncio.to_thread(db.collection.find_one, sort=[("_id", -1)])
        
        if result: 
            _id, last_ip_data = result.values() 
            return cls(**last_ip_data)
    
    async def save(self) -> bool: 
        data_dict = self.to_dict()
        res = await db.set(data_dict)
        return res
