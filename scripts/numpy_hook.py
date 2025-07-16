"""
Custom runtime hook to handle numpy docstring issues in PyInstaller.
"""


# Handle numpy docstring issues
def _handle_numpy_docstrings():
    """Patch numpy to handle docstring issues in frozen environment."""
    try:
        import numpy as np

        # Ensure numpy core modules are properly loaded
        import numpy.core.multiarray
        import numpy.core.numeric
        import numpy.core.umath
        import numpy.core.overrides

        # Patch the problematic function if needed
        if hasattr(np.core.overrides, "add_docstring"):
            original_add_docstring = np.core.overrides.add_docstring

            def safe_add_docstring(func, docstring):
                """Safe wrapper for add_docstring that handles non-string docstrings."""
                if isinstance(docstring, str):
                    return original_add_docstring(func, docstring)
                return func

            np.core.overrides.add_docstring = safe_add_docstring

    except ImportError:
        pass


# Call the handler
_handle_numpy_docstrings()
