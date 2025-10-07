from typing import List, Optional
from mcp_serializer.features.base.definitions import FunctionMetadata
from mcp_serializer.features.base.parsers import FunctionParser


class TestFunctionParser:
    def test_parse_function_with_google_style_docstring(self):
        def sample_function(name: str, age: int = 25, active: bool = True) -> str:
            """Process user information.

            This function processes user data and returns a formatted string.

            Args:
                name: The user's full name
                age: The user's age in years
                active: Whether the user account is active

            Returns:
                Formatted user information string
            """
            return f"{name} is {age} years old and {'active' if active else 'inactive'}"

        parser = FunctionParser(sample_function)
        metadata = parser.function_metadata

        assert metadata.name == "sample_function"
        assert metadata.title == "Process user information."
        assert (
            metadata.description
            == "This function processes user data and returns a formatted string."
        )
        assert metadata.return_type == str

        assert len(metadata.arguments) == 3

        name_arg = metadata.arguments[0]
        assert name_arg.name == "name"
        assert name_arg.type_hint == str
        assert name_arg.description == "The user's full name"
        assert name_arg.required == True
        assert name_arg.default == FunctionMetadata.empty

        age_arg = metadata.arguments[1]
        assert age_arg.name == "age"
        assert age_arg.type_hint == int
        assert age_arg.description == "The user's age in years"
        assert age_arg.required == False
        assert age_arg.default == 25

        active_arg = metadata.arguments[2]
        assert active_arg.name == "active"
        assert active_arg.type_hint == bool
        assert active_arg.required == False
        assert active_arg.default == True
        assert active_arg.description == "Whether the user account is active"

    def test_parse_function_with_numpy_style_docstring(self):
        def numpy_function(data: list, threshold: float) -> bool:
            """Analyze numerical data.

            Parameters
            ----------
            data : list
                Input data array to analyze
            threshold : float
                Minimum threshold value for analysis

            Returns
            -------
            bool
                True if data meets criteria
            """
            return max(data) > threshold

        parser = FunctionParser(numpy_function)
        metadata = parser.function_metadata

        assert metadata.name == "numpy_function"
        assert metadata.title == "Analyze numerical data."
        assert len(metadata.arguments) == 2

        data_arg = metadata.arguments[0]
        assert data_arg.name == "data"
        assert "Input data array" in data_arg.description

        threshold_arg = metadata.arguments[1]
        assert threshold_arg.name == "threshold"
        assert threshold_arg.description == "Minimum threshold value for analysis"

    def test_parse_function_with_sphinx_style_docstring(self):
        def sphinx_function(username: str, password: str = None):
            """Authenticate user credentials.

            :param username: The username to authenticate
            :param password: The user password, optional for guest access
            """
            return username == "admin" and password == "secret"

        parser = FunctionParser(sphinx_function)
        metadata = parser.function_metadata

        assert metadata.name == "sphinx_function"
        assert metadata.title == "Authenticate user credentials."
        assert len(metadata.arguments) == 2

        username_arg = metadata.arguments[0]
        assert username_arg.name == "username"
        assert username_arg.description == "The username to authenticate"
        assert username_arg.required == True

        password_arg = metadata.arguments[1]
        assert password_arg.name == "password"
        assert "optional for guest access" in password_arg.description
        assert password_arg.required == False

    def test_parse_function_without_docstring(self):
        def no_docstring_function(x: int, y: str = "default"):
            return f"{x}: {y}"

        parser = FunctionParser(no_docstring_function)
        metadata = parser.function_metadata

        assert metadata.name == "no_docstring_function"
        assert metadata.title is None
        assert metadata.description == ""
        assert len(metadata.arguments) == 2

        x_arg = metadata.arguments[0]
        assert x_arg.name == "x"
        assert x_arg.type_hint == int
        assert x_arg.description is None
        assert x_arg.required == True

        y_arg = metadata.arguments[1]
        assert y_arg.name == "y"
        assert y_arg.type_hint == str
        assert y_arg.required == False
        assert y_arg.default == "default"

    def test_parse_function_with_no_type_hints(self):
        def untyped_function(param1, param2="default"):
            """Simple function without type hints.

            Args:
                param1: First parameter
                param2: Second parameter with default
            """
            return param1 + str(param2)

        parser = FunctionParser(untyped_function)
        metadata = parser.function_metadata

        assert metadata.name == "untyped_function"
        assert len(metadata.arguments) == 2

        param1_arg = metadata.arguments[0]
        assert param1_arg.name == "param1"
        assert param1_arg.type_hint is str  # Default type hint is str
        assert param1_arg.description == "First parameter"
        assert param1_arg.required == True

        param2_arg = metadata.arguments[1]
        assert param2_arg.name == "param2"
        assert param2_arg.type_hint is str  # Default type hint is str
        assert param2_arg.required == False
        assert param2_arg.default == "default"

    def test_parse_class_method_excludes_self(self):
        class TestClass:
            def instance_method(self, value: int, name: str = "test") -> str:
                """Instance method with self parameter.

                Args:
                    value: Integer value
                    name: Name parameter
                """
                return f"{name}: {value}"

        instance = TestClass()
        parser = FunctionParser(instance.instance_method)
        metadata = parser.function_metadata

        assert len(metadata.arguments) == 2
        assert all(arg.name != "self" for arg in metadata.arguments)

        value_arg = metadata.arguments[0]
        assert value_arg.name == "value"
        assert value_arg.type_hint == int

        name_arg = metadata.arguments[1]
        assert name_arg.name == "name"
        assert name_arg.type_hint == str

    def test_function_metadata_properties(self):
        def func_with_required_and_optional(
            required_param: str, optional_param: int = 42
        ):
            """Function with mixed parameter requirements."""
            pass

        parser = FunctionParser(func_with_required_and_optional)
        metadata = parser.function_metadata

        assert metadata.has_required_arguments == True

        metadata_dict = metadata.to_dict()
        assert "name" in metadata_dict
        assert "arguments" in metadata_dict
        assert len(metadata_dict["arguments"]) == 2
        assert metadata_dict["arguments"][0]["required"] == True
        assert metadata_dict["arguments"][1]["required"] == False
