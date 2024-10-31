/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

struct InternalModelData {
    virtual ~InternalModelData() {}

    template <class T>
    T& asRef() {
        return dynamic_cast<T&>(*this);
    }

    template <class T>
    const T& asRef() const {
        return dynamic_cast<const T&>(*this);
    }
};

struct InternalImageModelData : public InternalModelData {
    InternalImageModelData(int width, int height) : inputImgWidth(width), inputImgHeight(height) {}

    int inputImgWidth;
    int inputImgHeight;
};

struct InternalScaleData : public InternalImageModelData {
    InternalScaleData(int width, int height, float scaleX, float scaleY)
        : InternalImageModelData(width, height),
          scaleX(scaleX),
          scaleY(scaleY) {}

    float scaleX;
    float scaleY;
};
