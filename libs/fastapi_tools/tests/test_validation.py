from geti_fastapi_tools.validation import RestApiValidator


class TestRestApiValidator:
    def test_schema_loader(self) -> None:
        """
        <b>Description:</b>
        To test if the schema loader properly resolves all $ref values in the underlying files.

        <b>Input data:</b>
        test.yaml file with a reference

        <b>Expected results:</b>
        Test passes if the resulting dictionary has resolved the very nested key.

        <b>Steps</b>
        1. Load test yaml file.
        2. Test if deepest key is available in the dictionary
        """

        schema_dict = RestApiValidator().load_schema_file_as_dict("tests/test_data/test_schema_1.yaml")
        assert (
            schema_dict["properties"]["annotations"]["items"]["properties"]["points"]["items"]["properties"]["x"][
                "type"
            ]
            == "number"
        )
        assert (
            schema_dict["properties"]["annotations"]["items"]["properties"]["points"]["items"]["properties"]["y"][
                "type"
            ]
            == "number"
        )
