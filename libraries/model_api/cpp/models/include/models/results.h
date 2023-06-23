/*
// Copyright (C) 2020-2023 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
*/

#pragma once
#include <map>
#include <memory>
#include <string>
#include <vector>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>

#include "internal_model_data.h"

struct MetaData;
struct ResultBase {
    ResultBase(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : frameId(frameId),
          metaData(metaData) {}
    virtual ~ResultBase() {}

    int64_t frameId;

    std::shared_ptr<MetaData> metaData;
    bool IsEmpty() {
        return frameId < 0;
    }

    template <class T>
    T& asRef() {
        return dynamic_cast<T&>(*this);
    }

    template <class T>
    const T& asRef() const {
        return dynamic_cast<const T&>(*this);
    }
};

struct InferenceResult : public ResultBase {
    std::shared_ptr<InternalModelData> internalModelData;
    std::map<std::string, ov::Tensor> outputsData;

    /// Returns the first output tensor
    /// This function is a useful addition to direct access to outputs list as many models have only one output
    /// @returns first output tensor
    ov::Tensor getFirstOutputTensor() {
        if (outputsData.empty()) {
            throw std::out_of_range("Outputs map is empty.");
        }
        return outputsData.begin()->second;
    }

    /// Returns true if object contains no valid data
    /// @returns true if object contains no valid data
    bool IsEmpty() {
        return outputsData.empty();
    }
};

struct ClassificationResult : public ResultBase {
    ClassificationResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}

    friend std::ostream& operator<< (std::ostream& os, const ClassificationResult& prediction) {
        for (const ClassificationResult::Classification& classification : prediction.topLabels) {
            os << classification << ", ";
        }
        try {
            os << prediction.saliency_map.get_shape() << ", ";
        } catch (ov::Exception&) {
            os << "[0], ";
        }
        try {
            os << prediction.feature_vector.get_shape();
        } catch (ov::Exception&) {
            os << "[0]";
        }
        return os;
    }

    explicit operator std::string() {
        std::stringstream ss;
        ss << *this;
        return ss.str();
    }

    struct Classification {
        unsigned int id;
        std::string label;
        float score;

        Classification(unsigned int id, const std::string& label, float score) : id(id), label(label), score(score) {}

        friend std::ostream& operator<< (std::ostream& os, const Classification& prediction) {
            return os << prediction.id << " (" << prediction.label << "): " << std::fixed << std::setprecision(3) << prediction.score;
        }
    };

    std::vector<Classification> topLabels;
    ov::Tensor saliency_map, feature_vector;  // Contan "saliency_map" and "feature_vector" model outputs if such exist
};

struct DetectedObject : public cv::Rect2f {
    size_t labelID;
    std::string label;
    float confidence;

    friend std::ostream& operator<< (std::ostream& os, const DetectedObject& detection)
    {
        return os << int(detection.x) << ", " << int(detection.y) << ", " << int(detection.x + detection.width)
            << ", " << int(detection.y + detection.height) << ", "
            << detection.labelID << " (" << detection.label << "): " << std::fixed << std::setprecision(3) << detection.confidence;
    }
};

struct DetectionResult : public ResultBase {
    DetectionResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<DetectedObject> objects;
    ov::Tensor saliency_map, feature_vector;  // Contan "saliency_map" and "feature_vector" model outputs if such exist

    friend std::ostream& operator<< (std::ostream& os, const DetectionResult& prediction) {
        for (const DetectedObject& obj : prediction.objects) {
            os << obj << "; ";
        }
        try {
            os << prediction.saliency_map.get_shape() << "; ";
        } catch (ov::Exception&) {
            os << "[0]; ";
        }
        try {
            os << prediction.feature_vector.get_shape();
        } catch (ov::Exception&) {
            os << "[0]";
        }
        return os;
    }

    explicit operator std::string() {
        std::stringstream ss;
        ss << *this;
        return ss.str();
    }
};

struct RetinaFaceDetectionResult : public DetectionResult {
    RetinaFaceDetectionResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : DetectionResult(frameId, metaData) {}
    std::vector<cv::Point2f> landmarks;
};

struct SegmentedObject : DetectedObject {
    cv::Mat mask;

    friend std::ostream& operator<< (std::ostream& stream, const SegmentedObject& segmentation)
    {
        stream << "(" << int(segmentation.x) << ", " << int(segmentation.y) << ", " << int(segmentation.x + segmentation.width)
            << ", " << int(segmentation.y + segmentation.height) << ", ";
        stream << std::fixed;
        stream << std::setprecision(3) << segmentation.confidence << ", ";
        stream << std::setprecision(-1) << segmentation.labelID << ", " << segmentation.label << ", " << cv::countNonZero(segmentation.mask > 0.5) << ")";
        return stream;
    }
};

struct SegmentedObjectWithRects : SegmentedObject {
    std::vector<cv::RotatedRect> rotated_rects;

    SegmentedObjectWithRects(const SegmentedObject& segmented_object) : SegmentedObject(segmented_object) {}

    friend std::ostream& operator<< (std::ostream& stream, const SegmentedObjectWithRects& segmentation)
    {
        stream << "(" << int(segmentation.x) << ", " << int(segmentation.y) << ", " << int(segmentation.x + segmentation.width)
            << ", " << int(segmentation.y + segmentation.height) << ", ";
        stream << std::fixed;
        stream << std::setprecision(3) << segmentation.confidence << ", ";
        stream << segmentation.labelID << ", " << segmentation.label << ", " << cv::countNonZero(segmentation.mask > 0.5);
        for (const cv::RotatedRect& rect : segmentation.rotated_rects) {
            stream << ", RotatedRect: " << rect.center.x << ' ' << rect.center.y << ' ' <<  rect.size.width << ' ' << rect.size.height << ' ' << rect.angle;
        }
        stream << ")";
        return stream;
    }
};

static inline std::vector<SegmentedObjectWithRects> add_rotated_rects(std::vector<SegmentedObject> segmented_objects) {
    std::vector<SegmentedObjectWithRects> objects_with_rects;
    objects_with_rects.reserve(segmented_objects.size());
    for (const SegmentedObject& segmented_object : segmented_objects) {
        objects_with_rects.push_back(SegmentedObjectWithRects{segmented_object});
        cv::Mat mask;
        segmented_object.mask.convertTo(mask, CV_8UC1);
        std::vector<std::vector<cv::Point>> contours;
        std::vector<cv::Vec4i> hierarchies;
        cv::findContours(mask, contours, hierarchies, cv::RETR_CCOMP, cv::CHAIN_APPROX_SIMPLE);
        if (hierarchies.empty()) {
            continue;
        }
        for (size_t i = 0; i < contours.size(); ++i) {
            if (hierarchies[i][3] != -1) {
                continue;
            }
            if (contours[i].size() <= 2 || cv::contourArea(contours[i]) < 1.0) {
                continue;
            }
            objects_with_rects.back().rotated_rects.push_back(cv::minAreaRect(contours[i]));
        }
    }
    return objects_with_rects;
}

struct InstanceSegmentationResult : ResultBase {
    InstanceSegmentationResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<SegmentedObject> segmentedObjects;
};

struct ImageResult : public ResultBase {
    ImageResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    cv::Mat resultImage;
    friend std::ostream& operator<< (std::ostream& os, const ImageResult& prediction) {
        cv::Mat predicted_mask[] = {prediction.resultImage};
        int nimages = 1;
        int *channels = nullptr;
        cv::Mat mask;
        cv::Mat outHist;
        int dims = 1;
        int histSize[] = {256};
        float range[] = {0, 256};
        const float *ranges[] = {range};
        cv::calcHist(predicted_mask, nimages, channels, mask, outHist, dims, histSize, ranges);

        os << std::fixed << std::setprecision(3);
        for (int i = 0; i < range[1]; ++i) {
            const float count = outHist.at<float>(i);
            if (count > 0) {
                os << i << ": " << count / prediction.resultImage.total() << ", ";
            }
        }
        return os;
    }
    explicit operator std::string() {
        std::stringstream ss;
        ss << *this;
        return ss.str();
    }
};

struct ImageResultWithSoftPrediction : public ImageResult {
    ImageResultWithSoftPrediction(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ImageResult(frameId, metaData) {}
    cv::Mat soft_prediction;
    ov::Tensor feature_vector;  // Contans "feature_vector" model output if such exists
    friend std::ostream& operator<< (std::ostream& os, const ImageResultWithSoftPrediction& prediction) {
        os << static_cast<const ImageResult&>(prediction) << '[';
        for (int i = 0; i < prediction.soft_prediction.dims; ++i) {
            os << prediction.soft_prediction.size[i] << ',';
        }
        os << prediction.soft_prediction.channels() << "], ";
        try {
            os << prediction.feature_vector.get_shape();
        } catch (ov::Exception&) {
            os << "[0]";
        }
        return os;
    }
};

struct Contour {
    std::string label;
    float probability;
    std::vector<cv::Point> shape;

    friend std::ostream& operator<< (std::ostream& os, const Contour& contour) {
        return os << contour.label << ": " << std::fixed << std::setprecision(3) << contour.probability << ", " << contour.shape.size();
    }
};


struct HumanPose {
    std::vector<cv::Point2f> keypoints;
    float score;
};

struct HumanPoseResult : public ResultBase {
    HumanPoseResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<HumanPose> poses;
};
