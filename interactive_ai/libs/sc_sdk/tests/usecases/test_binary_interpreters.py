# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import io

from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter, RAWBinaryInterpreter


class TestBinaryInterpreters:
    def test_raw_binary_interpreter(self) -> None:
        """
        <b>Description:</b>
        Checks that the RAW binary interpreter correctly reads binary data

        <b>Input data:</b>
        Binary string

        <b>Expected results:</b>
        Output from RAWBinaryInterpreter is the same as the input

        <b>Steps</b>
        1. Create input and BytesIO strea
        2. Interpret Binary data
        """
        raw_binary_interpreter = RAWBinaryInterpreter()
        input_bytes = b"some initial binary data"
        f = io.BytesIO(input_bytes)
        data = raw_binary_interpreter.interpret(f, filename="data.bin")
        assert data == input_bytes

    def test_numpy_binary_interpreter(self) -> None:
        """
        <b>Description:</b>
        Checks that the numpy binary interpreter correctly reads binary data

        <b>Input data:</b>
        Binary data of numpy array with shape [2,2,2]

        <b>Expected results:</b>
        NumpyBinaryInterpreter outputs a [2,2,2] numpy array

        <b>Steps</b>
        1. Create input and BytesIO stream
        2. Interpret the binary data as numpy array
        """
        numpy_binary_interpreter = NumpyBinaryInterpreter()

        input_bytes = (
            b"\x93\x4e\x55\x4d\x50\x59\x01\x00\x76\x00\x7b\x27\x64\x65\x73\x63\x72\x27"
            b"\x3a\x20\x27\x3c\x66\x38\x27\x2c\x20\x27\x66\x6f\x72\x74\x72\x61\x6e\x5f"
            b"\x6f\x72\x64\x65\x72\x27\x3a\x20\x46\x61\x6c\x73\x65\x2c\x20\x27\x73\x68"
            b"\x61\x70\x65\x27\x3a\x20\x28\x32\x2c\x20\x32\x2c\x20\x32\x29\x2c\x20\x7d"
            b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
            b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
            b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20"
            b"\x20\x0a\x00\x00\x00\x00\x00\x00\xf0\x3f\x00\x00\x00\x00\x00\x00\xf0\x3f"
            b"\x00\x00\x00\x00\x00\x00\xf0\x3f\x00\x00\x00\x00\x00\x00\xf0\x3f\x00\x00"
            b"\x00\x00\x00\x00\xf0\x3f\x00\x00\x00\x00\x00\x00\xf0\x3f\x00\x00\x00\x00"
            b"\x00\x00\xf0\x3f\x00\x00\x00\x00\x00\x00\xf0\x3f"
        )

        f = io.BytesIO(input_bytes)
        data = numpy_binary_interpreter.interpret(f, filename="data.npy")
        assert data.shape == (2, 2, 2)
