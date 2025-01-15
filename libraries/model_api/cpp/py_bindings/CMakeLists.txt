# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

set(DEV_MODULE Development.Module)

find_package(Python COMPONENTS Interpreter ${DEV_MODULE} REQUIRED)

execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)
find_package(nanobind CONFIG REQUIRED)


file(GLOB BINDINGS_SOURCES ./*.cpp)
file(GLOB BINDINGS_HEADERS ./*.hpp)

nanobind_add_module(py_model_api NB_STATIC STABLE_ABI LTO ${BINDINGS_SOURCES} ${BINDINGS_HEADERS})

target_link_libraries(py_model_api PRIVATE model_api)

nanobind_add_stub(
    py_model_api_stub
    MODULE py_model_api
    OUTPUT py_model_api.pyi
    PYTHON_PATH $<TARGET_FILE_DIR:py_model_api>
    DEPENDS py_model_api
)
