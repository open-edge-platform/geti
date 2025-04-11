"""
Tools for interacting with the logger
"""


def replace_wrapper_name(wrapper, new_name) -> None:  # noqa: ANN001
    """
    Replace the code name of a wrapper with a new name.

    Wrappers used in decorators have the downside that they obscure the call graph
    in profiling traces because every call to wrapped functions will be
    mediated by a single wrapping function. This means that the wrapper may
    have many callee/callers, especially widely logging wrappers.

    This function solves by allowing the decorator to provide a unique name
    to the wrapper for each decorated function.
    """

    # Extract the code of the function
    code = wrapper.__code__

    # Create a copy of the code with a new name.
    new_code = code.replace(co_name=new_name)

    # Finally, assign the updated code type containing the new name.
    wrapper.__code__ = new_code
