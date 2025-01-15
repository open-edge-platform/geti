/*
 * Copyright (C) 2025 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include <nanobind/ndarray.h>
#include <nanobind/operators.h>
#include <nanobind/stl/map.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/vector.h>

#include "models/classification_model.h"
#include "models/results.h"
#include "py_utils.hpp"

namespace pyutils = vision::nanobind::utils;

void init_classification(nb::module_& m) {
    nb::class_<ClassificationResult::Classification>(m, "Classification")
        .def(nb::init<unsigned int, const std::string, float>())
        .def_rw("id", &ClassificationResult::Classification::id)
        .def_rw("label", &ClassificationResult::Classification::label)
        .def_rw("score", &ClassificationResult::Classification::score);

    nb::class_<ClassificationResult, ResultBase>(m, "ClassificationResult")
        .def(nb::init<>())
        .def_ro("topLabels", &ClassificationResult::topLabels)
        .def("__repr__", &ClassificationResult::operator std::string)
        .def_prop_ro(
            "feature_vector",
            [](ClassificationResult& r) {
                if (!r.feature_vector) {
                    return nb::ndarray<float, nb::numpy, nb::c_contig>();
                }

                return nb::ndarray<float, nb::numpy, nb::c_contig>(r.feature_vector.data(),
                                                                   r.feature_vector.get_shape().size(),
                                                                   r.feature_vector.get_shape().data());
            },
            nb::rv_policy::reference_internal)
        .def_prop_ro(
            "saliency_map",
            [](ClassificationResult& r) {
                if (!r.saliency_map) {
                    return nb::ndarray<float, nb::numpy, nb::c_contig>();
                }

                return nb::ndarray<float, nb::numpy, nb::c_contig>(r.saliency_map.data(),
                                                                   r.saliency_map.get_shape().size(),
                                                                   r.saliency_map.get_shape().data());
            },
            nb::rv_policy::reference_internal);

    nb::class_<ClassificationModel, ImageModel>(m, "ClassificationModel")
        .def_static(
            "create_model",
            [](const std::string& model_path,
               const std::map<std::string, nb::object>& configuration,
               bool preload,
               const std::string& device) {
                auto ov_any_config = ov::AnyMap();
                for (const auto& item : configuration) {
                    ov_any_config[item.first] = pyutils::py_object_to_any(item.second, item.first);
                }

                return ClassificationModel::create_model(model_path, ov_any_config, preload, device);
            },
            nb::arg("model_path"),
            nb::arg("configuration") = ov::AnyMap({}),
            nb::arg("preload") = true,
            nb::arg("device") = "AUTO")

        .def("__call__",
             [](ClassificationModel& self, const nb::ndarray<>& input) {
                 return self.infer(pyutils::wrap_np_mat(input));
             })
        .def("infer_batch", [](ClassificationModel& self, const std::vector<nb::ndarray<>> inputs) {
            std::vector<ImageInputData> input_mats;
            input_mats.reserve(inputs.size());

            for (const auto& input : inputs) {
                input_mats.push_back(pyutils::wrap_np_mat(input));
            }

            return self.inferBatch(input_mats);
        });
}
