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

        # Use the new API instead of deprecated numpy.core.overrides
        try:
            import numpy._core.overrides

            overrides_module = np._core.overrides
        except ImportError:
            # Fallback to old API if new one is not available
            import numpy.core.overrides

            overrides_module = np.core.overrides

        # Patch the problematic function if needed
        if hasattr(overrides_module, "add_docstring"):
            original_add_docstring = overrides_module.add_docstring

            def safe_add_docstring(func, docstring):
                """Safe wrapper for add_docstring that handles non-string docstrings."""
                if isinstance(docstring, str):
                    return original_add_docstring(func, docstring)
                return func

            overrides_module.add_docstring = safe_add_docstring

    except ImportError:
        pass


# Call the handler
_handle_numpy_docstrings()
