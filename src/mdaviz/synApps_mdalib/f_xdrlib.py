#!/usr/bin/env python3
"""
Fallback xdrlib implementation for Python 3.13+ compatibility.

This module provides a minimal implementation of the xdrlib functionality
needed by the MDA file reader when the standard xdrlib module is not available
(deprecated and removed in Python 3.13+).

Based on the original xdrlib implementation but simplified for our specific needs.
"""

import struct
import sys
from typing import Any, List, Optional, Union


class Error(Exception):
    """Exception raised for XDR errors."""
    pass


class ConversionError(Error):
    """Exception raised for conversion errors."""
    pass


class Packer:
    """XDR packer for binary data serialization."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the packer buffer."""
        self._buffer = bytearray()

    def get_buffer(self) -> bytes:
        """Get the packed data as bytes."""
        return bytes(self._buffer)

    def pack_uint(self, x: int) -> None:
        """Pack an unsigned 32-bit integer."""
        if not isinstance(x, int) or x < 0 or x > 0xFFFFFFFF:
            raise ConversionError("uint must be 0 <= uint <= 2**32-1")
        self._buffer.extend(struct.pack(">I", x))

    def pack_int(self, x: int) -> None:
        """Pack a signed 32-bit integer."""
        if not isinstance(x, int) or x < -0x80000000 or x > 0x7FFFFFFF:
            raise ConversionError("int must be -2**31 <= int <= 2**31-1")
        self._buffer.extend(struct.pack(">i", x))

    def pack_hyper(self, x: int) -> None:
        """Pack a signed 64-bit integer."""
        if not isinstance(x, int) or x < -0x8000000000000000 or x > 0x7FFFFFFFFFFFFFFF:
            raise ConversionError("hyper must be -2**63 <= hyper <= 2**63-1")
        self._buffer.extend(struct.pack(">q", x))

    def pack_float(self, x: float) -> None:
        """Pack a 32-bit float."""
        if not isinstance(x, (int, float)):
            raise ConversionError("float must be a number")
        self._buffer.extend(struct.pack(">f", float(x)))

    def pack_double(self, x: float) -> None:
        """Pack a 64-bit float."""
        if not isinstance(x, (int, float)):
            raise ConversionError("double must be a number")
        self._buffer.extend(struct.pack(">d", float(x)))

    def pack_fstring(self, n: int, s: Union[str, bytes]) -> None:
        """Pack a fixed length string."""
        if not isinstance(n, int) or n < 0:
            raise ConversionError("fstring length must be >= 0")
        if isinstance(s, str):
            s = s.encode('utf-8')
        if len(s) != n:
            raise ConversionError("fstring length mismatch")
        self._buffer.extend(s)

    def pack_fopaque(self, n: int, data: bytes) -> None:
        """Pack fixed length opaque data."""
        if not isinstance(n, int) or n < 0:
            raise ConversionError("fopaque length must be >= 0")
        if len(data) != n:
            raise ConversionError("fopaque length mismatch")
        self._buffer.extend(data)

    def pack_string(self, s: Union[str, bytes]) -> None:
        """Pack a variable length string."""
        if isinstance(s, str):
            s = s.encode('utf-8')
        self.pack_uint(len(s))
        self._buffer.extend(s)
        # Pad to 4-byte boundary
        padding = (4 - (len(s) % 4)) % 4
        if padding:
            self._buffer.extend(b'\x00' * padding)

    def pack_opaque(self, data: bytes) -> None:
        """Pack variable length opaque data."""
        self.pack_uint(len(data))
        self._buffer.extend(data)
        # Pad to 4-byte boundary
        padding = (4 - (len(data) % 4)) % 4
        if padding:
            self._buffer.extend(b'\x00' * padding)

    def pack_bytes(self, data: bytes) -> None:
        """Pack variable length bytes (alias for pack_opaque)."""
        self.pack_opaque(data)

    def pack_list(self, list_: List[Any], pack_item) -> None:
        """Pack a list of items."""
        self.pack_uint(len(list_))
        for item in list_:
            pack_item(item)

    def pack_array(self, list_: List[Any], pack_item) -> None:
        """Pack an array of items."""
        for item in list_:
            pack_item(item)


class Unpacker:
    """XDR unpacker for binary data deserialization."""

    def __init__(self, data: bytes):
        self.reset(data)

    def reset(self, data: bytes) -> None:
        """Reset the unpacker with new data."""
        self._data = data
        self._position = 0

    def get_position(self) -> int:
        """Get the current position in the data."""
        return self._position

    def set_position(self, position: int) -> None:
        """Set the position in the data."""
        if position < 0 or position > len(self._data):
            raise Error("position out of range")
        self._position = position

    def get_buffer(self) -> bytes:
        """Get the remaining data as bytes."""
        return self._data[self._position:]

    def done(self) -> None:
        """Check if all data has been consumed."""
        if self._position < len(self._data):
            raise Error("unpacked data too short")

    def unpack_uint(self) -> int:
        """Unpack an unsigned 32-bit integer."""
        if self._position + 4 > len(self._data):
            raise Error("data too short")
        value = struct.unpack(">I", self._data[self._position:self._position + 4])[0]
        self._position += 4
        return value

    def unpack_int(self) -> int:
        """Unpack a signed 32-bit integer."""
        if self._position + 4 > len(self._data):
            raise Error("data too short")
        value = struct.unpack(">i", self._data[self._position:self._position + 4])[0]
        self._position += 4
        return value

    def unpack_hyper(self) -> int:
        """Unpack a signed 64-bit integer."""
        if self._position + 8 > len(self._data):
            raise Error("data too short")
        value = struct.unpack(">q", self._data[self._position:self._position + 8])[0]
        self._position += 8
        return value

    def unpack_float(self) -> float:
        """Unpack a 32-bit float."""
        if self._position + 4 > len(self._data):
            raise Error("data too short")
        value = struct.unpack(">f", self._data[self._position:self._position + 4])[0]
        self._position += 4
        return value

    def unpack_double(self) -> float:
        """Unpack a 64-bit float."""
        if self._position + 8 > len(self._data):
            raise Error("data too short")
        value = struct.unpack(">d", self._data[self._position:self._position + 8])[0]
        self._position += 8
        return value

    def unpack_fstring(self, n: int) -> bytes:
        """Unpack a fixed length string."""
        if self._position + n > len(self._data):
            raise Error("data too short")
        value = self._data[self._position:self._position + n]
        self._position += n
        return value

    def unpack_fopaque(self, n: int) -> bytes:
        """Unpack fixed length opaque data."""
        return self.unpack_fstring(n)

    def unpack_string(self) -> bytes:
        """Unpack a variable length string."""
        length = self.unpack_uint()
        if self._position + length > len(self._data):
            raise Error("data too short")
        value = self._data[self._position:self._position + length]
        self._position += length
        # Skip padding to 4-byte boundary
        padding = (4 - (length % 4)) % 4
        if padding:
            self._position += padding
        return value

    def unpack_opaque(self) -> bytes:
        """Unpack variable length opaque data."""
        return self.unpack_string()

    def unpack_bytes(self) -> bytes:
        """Unpack variable length bytes (alias for unpack_opaque)."""
        return self.unpack_opaque()

    def unpack_list(self, unpack_item) -> List[Any]:
        """Unpack a list of items."""
        length = self.unpack_uint()
        result = []
        for _ in range(length):
            result.append(unpack_item())
        return result

    def unpack_array(self, unpack_item, n: int) -> list:
        """Unpack an array of items, matching the xdrlib signature used in mda.py."""
        return [unpack_item() for _ in range(n)]


# Convenience functions for common operations
def pack_uint(x: int) -> bytes:
    """Pack a single unsigned integer."""
    p = Packer()
    p.pack_uint(x)
    return p.get_buffer()


def pack_int(x: int) -> bytes:
    """Pack a single signed integer."""
    p = Packer()
    p.pack_int(x)
    return p.get_buffer()


def pack_float(x: float) -> bytes:
    """Pack a single float."""
    p = Packer()
    p.pack_float(x)
    return p.get_buffer()


def pack_double(x: float) -> bytes:
    """Pack a single double."""
    p = Packer()
    p.pack_double(x)
    return p.get_buffer()


def pack_string(s: Union[str, bytes]) -> bytes:
    """Pack a single string."""
    p = Packer()
    p.pack_string(s)
    return p.get_buffer()


def unpack_uint(data: bytes) -> int:
    """Unpack a single unsigned integer."""
    u = Unpacker(data)
    return u.unpack_uint()


def unpack_int(data: bytes) -> int:
    """Unpack a single signed integer."""
    u = Unpacker(data)
    return u.unpack_int()


def unpack_float(data: bytes) -> float:
    """Unpack a single float."""
    u = Unpacker(data)
    return u.unpack_float()


def unpack_double(data: bytes) -> float:
    """Unpack a single double."""
    u = Unpacker(data)
    return u.unpack_double()


def unpack_string(data: bytes) -> bytes:
    """Unpack a single string."""
    u = Unpacker(data)
    return u.unpack_string()
