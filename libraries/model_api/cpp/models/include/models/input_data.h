/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <opencv2/opencv.hpp>

struct InputData {
    virtual ~InputData() {}

    template <class T>
    T& asRef() {
        return dynamic_cast<T&>(*this);
    }

    template <class T>
    const T& asRef() const {
        return dynamic_cast<const T&>(*this);
    }
};

struct ImageInputData : public InputData {
    cv::Mat inputImage;

    ImageInputData() {}
    ImageInputData(const cv::Mat& img) {
        inputImage = img;
    }
};
