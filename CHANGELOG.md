# Changelog

All notable changes to this project will be documented in this file.

## Enhanced Type System and Response Architecture
Version: 1.2.0
Date: 25 Dec, 2025

Updates:
* **Enhanced Type Casting System**: Significantly expanded `cast_python_type` function with comprehensive support for:
  - Union and Optional types
  - Generic collections (List, Dict, Set, Tuple, FrozenSet)
  - Date/time types (datetime, date, time, timedelta)
  - Special types (UUID, Path, Decimal, complex, Enum)
  - Pydantic BaseModel
  - Base64 encoded bytes
  - Nested and complex type combinations
* **Response Architecture**: Introduced `ResponseContext` and `ResponseEntry` classes for better request-response tracking:
  - `ResponseContext` provides centralized response data and history tracking
  - `ResponseEntry` captures individual request-response pairs with metadata
  - Improved support for batch requests and notifications
  - Better error context and debugging capabilities
* **Result Schema**: Changed `ResultSchema.content` default from `None` to `[]` for consistent response structure
* **Error Handling**: Simplified error response generation by removing redundant `model_dump()` calls
* **Documentation Improvements**:
  - Updated README with comprehensive `ResponseContext` usage examples
  - Added detailed docstrings for `process_request` method
  - Updated all result imports to use `mcp_serializer.results` package
  - Clarified Pydantic BaseModel properties in documentation
* **Parser Enhancements**: Improved NumPy-style docstring parsing with better regex patterns
* **Test Coverage**: Added comprehensive test suite for enhanced type casting system (75+ new test cases)
* **Code Quality**: Improved type hints and removed unused code

## Patch fixes
Version: 1.1.0
Date: 2 Nov, 2025

Updates:
* Fixed class name consistency: Updated "Initializer" to "MCPInitializer" throughout documentation
* Removed incorrect "nextCursor" fields from tools/list and prompts/list response examples

## Initial Documentation Release
Version: 1.0.0
Date: 2 Nov, 2025

Updates:
* Created comprehensive README documentation from test specifications
* Added installation instructions
* Documented feature registration (resources, tools, and prompts)
* Added initializer setup guide
* Included serializer creation and usage instructions
* Provided detailed examples for all MCP operations:
  - Initialization
  - Tools (list, call with different return types)
  - Prompts (list, get with/without arguments)
  - Resources (list, templates, read)
  - Error handling
  - Batch requests
