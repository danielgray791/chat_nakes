from .mongodb import MongoDB

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
