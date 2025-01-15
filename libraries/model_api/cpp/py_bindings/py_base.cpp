/*
 * Copyright (C) 2025 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <openvino/openvino.hpp>

#include "models/image_model.h"
#include "models/results.h"

namespace nb = nanobind;

void init_base_modules(nb::module_& m) {
    nb::class_<ResultBase>(m, "ResultBase").def(nb::init<>());

    nb::class_<ModelBase>(m, "ModelBase")
        .def("load", [](ModelBase& self, const std::string& device, size_t num_infer_requests) {
            auto core = ov::Core();
            self.load(core, device, num_infer_requests);
        });

    nb::class_<ImageModel, ModelBase>(m, "ImageModel");
}
