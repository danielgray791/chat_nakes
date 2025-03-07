import asyncio

from provider import Corcel, Artifacts, Scira, get_instance, providers
from dataclasses import dataclass
from typing import Dict, Optional, List, Any, Union
from mongodb import MongoDB

DEFAULT_PROVIDER = providers["scira"]
db = MongoDB()

def pretty_class(
    obj: object, 
    indent_width: int = 2, 
    iter: int = 1
) -> str: 
    """
    Return a string representation of the given object with a pretty-printed format.

    Parameters:
        obj (Any): The object to be pretty-printed.
        indent_width (int): The number of spaces for each level of indentation (default is 2).
        iter (int): The current iteration level used for indentation (default is 1).

    Returns:
        str: A string representing the object in a pretty-printed format.
    """
    obj_name = obj.__class__.__name__
    result = f"{obj_name}("

    for key, value in obj.__dict__.items():
        indent = " " * (indent_width * iter)

        if hasattr(value, "__dict__"):
            result += f"\n{indent}{key}=" + pretty_class(value, indent_width, iter + 1) + ","
        else: 
            value = f"\"{value}\"" if isinstance(value, str) else value
            result += f"\n{indent}{key}={value},"
    
    # remove extra comma
    result = result[:-1]

    outer_indent = " " * (indent_width * (iter - 1))
    result += f"\n{outer_indent})"
    
    return result


@dataclass
class Provider:
    name: str
    item_name: str 

    def to_dict(self) -> Dict[str, str]:
        return {
            'name': self.name,
            'item_name': self.item_name
        }
    
    def __str__(self) -> str: 
        return pretty_class(self)
    
@dataclass
class Config:
    model: str
    model_ins: Union[Corcel, Artifacts, Scira]
    vision: bool
    provider: Provider
    
    def to_dict(self) -> Dict[str, any]: 
        return {
            'model': self.model,
            'vision': self.vision,
            'provider': self.provider.to_dict()  # Convert Provider to dict
        }
    
    def __str__(self) -> str: 
        return pretty_class(self)

@dataclass
class ChatUser: 
    id: str
    name: str
    config: Config
    history: Dict[str, List[any]]
    menu: str
    action: str

    def __init__(
            self, 
            user_id: str, 
            name: str, 
            config: Optional[Config] = None, 
            history: Optional[Dict[str, List[any]]] = {},
            menu: Optional[str] = "", 
            action: Optional[str] = "",
        ): 

        self.id = user_id
        self.name = name
        self.config = config

        if config is None: 
            self.config = Config(
                model=DEFAULT_PROVIDER.default_model,
                model_ins=Artifacts(),
                vision=True,
                provider=Provider(
                    name=DEFAULT_PROVIDER.name,
                    item_name=DEFAULT_PROVIDER.item_name
                )
            )

        self.menu = menu
        self.action = action
        self.history = history
        if not self.history: 
            for provider in providers.values(): 
                self.history[provider.item_name] = []

    def to_dict(self) -> Dict[str, any]:
        return {
            'id': self.id,
            'name': self.name,
            'config': self.config.to_dict(),  # Convert Config to dict
            'menu': self.menu,
            'action': self.action,
            'history': self.history
        }

    async def save(self) -> bool: 
        item_name = self.config.provider.item_name
        if not self.history.get(item_name): 
            self.history[item_name] = []

        history = self.history[item_name]

        if len(history) >= 40: 
            history = history[:2] + history[20:]

        data_dict = self.to_dict()
        res = await db.set(data_dict)
        return res
    
    @classmethod
    async def get(cls, user_id: str) -> Optional['ChatUser']: 
        user_id = str(user_id)
        _id, user = await db.get(user_id)

        if user is None: 
            return None
        
        config = user["config"]
        provider = config["provider"]
        provider_item_name = provider["item_name"]
        model_ins = get_instance(provider_item_name)

        return cls(
            user_id=str(user["id"]),
            name=user["name"],
            config=Config(
                model=config["model"],
                model_ins=model_ins,
                vision=config["vision"],
                provider=Provider(
                    name=provider["name"],
                    item_name=provider["item_name"]
                )
            ),
            menu=user["menu"],
            action=user["action"],
            history=user["history"],
        )

    def __str__(self) -> str: 
        return pretty_class(self)

async def main(): 
    # user_data_dict = {
    #     "name": "My Time Is Up",
    #     "chat_config": {
    #         "model": "gpt-4o",
    #         "provider": {
    #             "name": "Corcel",
    #             "item_name": "corcel"
    #         }
    #     },
    #     "menu": "",
    #     "action": ""
    #     "history": {}
    # }

    user = ChatUser(user_id="7251930183", name="Dusk Till Dawn")
    print("[Chat User]")
    print(user)

    # print("[Saving Chat User]")
    # await user.save()

    # user_from_db = await ChatUser.get(user.id)
    # print("[Chat User From DB]")
    # print(user_from_db)

if __name__ == "__main__": 
    asyncio.run(main())
