import re

from .corcel import Corcel
from .artifacts import Artifacts
from .scira import Scira

from dataclasses import dataclass
from typing import Dict, List, Union

def escape(text, flag=0): 
    def find_all_index(str, pattern):
        index_list = [0]
        for match in re.finditer(pattern, str, re.MULTILINE):
            if match.group(1) != None:
                start = match.start(1)
                end = match.end(1)
                index_list += [start, end]
        index_list.append(len(str))
        return index_list

    def replace_all(text, pattern, function):
        poslist = [0]
        strlist = []
        originstr = []
        poslist = find_all_index(text, pattern)
        for i in range(1, len(poslist[:-1]), 2):
            start, end = poslist[i : i + 2]
            strlist.append(function(text[start:end]))
        for i in range(0, len(poslist), 2):
            j, k = poslist[i : i + 2]
            originstr.append(text[j:k])
        if len(strlist) < len(originstr):
            strlist.append("")
        else:
            originstr.append("")
        new_list = [item for pair in zip(originstr, strlist) for item in pair]
        return "".join(new_list)

    def escapeshape(text):
        return "▎*" + text.split()[1] + "*"

    def escapeminus(text):
        return "\\" + text

    def escapebackquote(text):
        return r"\`\`"

    def escapeplus(text):
        return "\\" + text

    # In all other places characters
    # _ * [ ] ( ) ~ ` > # + - = | { } . !
    # must be escaped with the preceding character '\'.
    text = re.sub(r"\\\[", "@->@", text)
    text = re.sub(r"\\\]", "@<-@", text)
    text = re.sub(r"\\\(", "@-->@", text)
    text = re.sub(r"\\\)", "@<--@", text)
    if flag:
        text = re.sub(r"\\\\", "@@@", text)
    text = re.sub(r"\\", r"\\\\", text)
    if flag:
        text = re.sub(r"\@{3}", r"\\\\", text)
    text = re.sub(r"_", "\_", text)
    text = re.sub(r"\*{2}(.*?)\*{2}", "@@@\\1@@@", text)
    text = re.sub(r"\n{1,2}\*\s", "\n\n• ", text)
    text = re.sub(r"\*", "\*", text)
    text = re.sub(r"\@{3}(.*?)\@{3}", "*\\1*", text)
    text = re.sub(r"\!?\[(.*?)\]\((.*?)\)", "@@@\\1@@@^^^\\2^^^", text)
    text = re.sub(r"\[", "\[", text)
    text = re.sub(r"\]", "\]", text)
    text = re.sub(r"\(", "\(", text)
    text = re.sub(r"\)", "\)", text)
    text = re.sub(r"\@\-\>\@", "\[", text)
    text = re.sub(r"\@\<\-\@", "\]", text)
    text = re.sub(r"\@\-\-\>\@", "\(", text)
    text = re.sub(r"\@\<\-\-\@", "\)", text)
    text = re.sub(r"\@{3}(.*?)\@{3}\^{3}(.*?)\^{3}", "[\\1](\\2)", text)
    text = re.sub(r"~", "\~", text)
    text = re.sub(r">", "\>", text)
    text = replace_all(text, r"(^#+\s.+?$)|```[\D\d\s]+?```", escapeshape)
    text = re.sub(r"#", "\#", text)
    text = replace_all(
        text, r"(\+)|\n[\s]*-\s|```[\D\d\s]+?```|`[\D\d\s]*?`", escapeplus
    )
    text = re.sub(r"\n{1,2}(\s*)-\s", "\n\n\\1• ", text)
    text = re.sub(r"\n{1,2}(\s*\d{1,2}\.\s)", "\n\n\\1", text)
    text = replace_all(
        text, r"(-)|\n[\s]*-\s|```[\D\d\s]+?```|`[\D\d\s]*?`", escapeminus
    )
    text = re.sub(r"```([\D\d\s]+?)```", "@@@\\1@@@", text)
    text = replace_all(text, r"(``)", escapebackquote)
    text = re.sub(r"\@{3}([\D\d\s]+?)\@{3}", "```\\1```", text)
    text = re.sub(r"=", "\=", text)
    text = re.sub(r"\|", "\|", text)
    text = re.sub(r"{", "\{", text)
    text = re.sub(r"}", "\}", text)
    text = re.sub(r"\.", "\.", text)
    text = re.sub(r"!", "\!", text)
    return text

def split_message(message, max_length=4096):
    chunks = []
    start = 0
    length = len(message)
    
    while start < length:
        end = start + max_length
        if end >= length:
            # The rest of the message fits into the last chunk
            chunks.append(message[start:])
            break
        else:
            # Find the last space character before the end index
            last_space = message.rfind(' ', start, end)
            if last_space == -1 or last_space <= start:
                # Can't find a space to split before max_length
                next_space = message.find(' ', end)
                if next_space != -1:
                    # Split at the next available space after max_length
                    chunks.append(message[start:next_space])
                    start = next_space + 1  # Move past the space
                else:
                    # No more spaces; take the rest of the message
                    chunks.append(message[start:])
                    break
            else:
                # Split at the last space before max_length
                chunks.append(message[start:last_space])
                start = last_space + 1  # Move past the space
    return chunks


@dataclass
class Model: 
    number: int
    name: str
    id: str
    vision: bool

@dataclass
class Provider:
    name: str
    item_name: str
    default_model: str
    models: List[Model]

    def get_model(self, model_name: str) -> Model: 
        for model in self.models: 
            if model.name == model_name: 
                return model
        return None

providers = {
    "corcel": Provider(
        name="NAKES V1",
        item_name="corcel",
        default_model="GPT 4 dot 0",
        models=[
            Model(number=1, name="GPT 4 dot 0", id="gpt-4o", vision=False),
            Model(number=2, name="Claude 3 dot 5 Sonnet", id="claude-3-5-sonnet-20241022", vision=False),
            Model(number=3, name="Cortext Ultra", id="cortext-ultra",  vision=False)
        ]
    ),
    "artifacts": Provider(
        name="NAKES V2",
        item_name="artifacts",
        default_model="GPT 4 dot 5 preview",
        models=[
            Model(number=1, name="Claude 3 dot 7 Sonnet", id="claude-3-7-sonnet-latest", vision=True),
            Model(number=2, name="Claude 3 dot 5 Sonnet", id="claude-3-5-sonnet-latest", vision=True),
            Model(number=3, name="Claude 3 dot 5 Haiku", id="claude-3-5-haiku-latest", vision=True),
            Model(number=4, name="GPT 4 dot 1", id="gpt-4.1", vision=True),
            Model(number=5, name="GPT 4 dot 1 mini", id="gpt-4.1-mini", vision=True),
            Model(number=6, name="GPT 4 dot 1 nano", id="gpt-4.1-nano", vision=True),
            Model(number=7, name="GPT 4 dot 5 preview", id="gpt-4.5-preview", vision=True),
            Model(number=8, name="Gemini 2 dot 5 Pro Exp", id="gemini-2.5-pro-exp-03-25", vision=False),
        ]
    ),
    "scira": Provider(
        name="NAKES V3",
        item_name="scira",
        default_model="GPT o4 Mini",
        models=[
            Model(number=1, name="GPT 4o latest", id="scira-4o", vision=True),
            Model(number=2, name="GPT o4 Mini", id="scira-o4-mini", vision=True),
            Model(number=3, name="Grok 3 dot 0 mini", id="scira-grok-3-mini", vision=True),
            Model(number=4, name="Grok 3 dot 0", id="scira-default", vision=True),
            Model(number=5, name="Gemini 2 dot 5 Flash", id="scira-google", vision=True),
            Model(number=6, name="Gemini 2 dot 5 Pro", id="scira-google-pro", vision=True),
            Model(number=7, name="Sonnet 4 dot 0 Thinking", id="scira-anthropic-thinking", vision=True),
            Model(number=8, name="Sonnet 4 dot 0", id="scira-anthropic", vision=True),  
        ]
    )
}

corcel_ins = Corcel()
artifacts_ins = Artifacts()
scira_ins = Scira()

def get_instance(name: str = "corcel"): 
    return (
        corcel_ins if name == "corcel"
        else artifacts_ins if name == "artifacts"
        else scira_ins if name == "scira"
        else None
    )


