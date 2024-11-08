/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <map>
#include <memory>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>
#include <string>
#include <vector>

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

struct AnomalyResult : public ResultBase {
    AnomalyResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    cv::Mat anomaly_map;
    std::vector<cv::Rect> pred_boxes;
    std::string pred_label;
    cv::Mat pred_mask;
    double pred_score;

    friend std::ostream& operator<<(std::ostream& os, const AnomalyResult& prediction) {
        double min_anomaly_map, max_anomaly_map;
        cv::minMaxLoc(prediction.anomaly_map, &min_anomaly_map, &max_anomaly_map);
        double min_pred_mask, max_pred_mask;
        cv::minMaxLoc(prediction.pred_mask, &min_pred_mask, &max_pred_mask);
        os << "anomaly_map min:" << min_anomaly_map << " max:" << max_anomaly_map << ";";
        os << "pred_score:" << std::fixed << std::setprecision(1) << prediction.pred_score << ";";
        os << "pred_label:" << prediction.pred_label << ";";
        os << std::fixed << std::setprecision(0) << "pred_mask min:" << min_pred_mask << " max:" << max_pred_mask
           << ";";

        if (!prediction.pred_boxes.empty()) {
            os << "pred_boxes:";
            for (const cv::Rect& box : prediction.pred_boxes) {
                os << box << ",";
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

    friend std::ostream& operator<<(std::ostream& os, const ClassificationResult& prediction) {
        for (const ClassificationResult::Classification& classification : prediction.topLabels) {
            os << classification << ", ";
        }
        try {
            os << prediction.saliency_map.get_shape() << ", ";
        } catch (ov::Exception&) {
            os << "[0], ";
        }
        try {
            os << prediction.feature_vector.get_shape() << ", ";
        } catch (ov::Exception&) {
            os << "[0], ";
        }
        try {
            os << prediction.raw_scores.get_shape();
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

        friend std::ostream& operator<<(std::ostream& os, const Classification& prediction) {
            return os << prediction.id << " (" << prediction.label << "): " << std::fixed << std::setprecision(3)
                      << prediction.score;
        }
    };

    std::vector<Classification> topLabels;
    ov::Tensor saliency_map, feature_vector,
        raw_scores;  // Contains "raw_scores", "saliency_map" and "feature_vector" model outputs if such exist
};

struct DetectedObject : public cv::Rect2f {
    size_t labelID;
    std::string label;
    float confidence;

    friend std::ostream& operator<<(std::ostream& os, const DetectedObject& detection) {
        return os << int(detection.x) << ", " << int(detection.y) << ", " << int(detection.x + detection.width) << ", "
                  << int(detection.y + detection.height) << ", " << detection.labelID << " (" << detection.label
                  << "): " << std::fixed << std::setprecision(3) << detection.confidence;
    }
};

struct DetectionResult : public ResultBase {
    DetectionResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<DetectedObject> objects;
    ov::Tensor saliency_map, feature_vector;  // Contan "saliency_map" and "feature_vector" model outputs if such exist

    friend std::ostream& operator<<(std::ostream& os, const DetectionResult& prediction) {
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

    friend std::ostream& operator<<(std::ostream& os, const SegmentedObject& prediction) {
        return os << static_cast<const DetectedObject&>(prediction) << ", " << cv::countNonZero(prediction.mask > 0.5);
    }
};

struct SegmentedObjectWithRects : SegmentedObject {
    cv::RotatedRect rotated_rect;

    SegmentedObjectWithRects(const SegmentedObject& segmented_object) : SegmentedObject(segmented_object) {}

    friend std::ostream& operator<<(std::ostream& os, const SegmentedObjectWithRects& prediction) {
        os << static_cast<const SegmentedObject&>(prediction) << std::fixed << std::setprecision(3);
        auto rect = prediction.rotated_rect;
        os << ", RotatedRect: " << rect.center.x << ' ' << rect.center.y << ' ' << rect.size.width << ' '
           << rect.size.height << ' ' << rect.angle;
        return os;
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
        cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

        std::vector<cv::Point> contour = {};
        for (size_t i = 0; i < contours.size(); i++) {
            contour.insert(contour.end(), contours[i].begin(), contours[i].end());
        }
        if (contour.size() > 0) {
            std::vector<cv::Point> hull;
            cv::convexHull(contour, hull);
            objects_with_rects.back().rotated_rect = cv::minAreaRect(hull);
        }
    }
    return objects_with_rects;
}

struct InstanceSegmentationResult : ResultBase {
    InstanceSegmentationResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<SegmentedObject> segmentedObjects;
    // Contan per class saliency_maps and "feature_vector" model output if feature_vector exists
    std::vector<cv::Mat_<std::uint8_t>> saliency_map;
    ov::Tensor feature_vector;
};

struct ImageResult : public ResultBase {
    ImageResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    cv::Mat resultImage;
    friend std::ostream& operator<<(std::ostream& os, const ImageResult& prediction) {
        cv::Mat predicted_mask[] = {prediction.resultImage};
        int nimages = 1;
        int* channels = nullptr;
        cv::Mat mask;
        cv::Mat outHist;
        int dims = 1;
        int histSize[] = {256};
        float range[] = {0, 256};
        const float* ranges[] = {range};
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
    // Contain per class saliency_maps and "feature_vector" model output if feature_vector exists
    cv::Mat saliency_map;  // Requires return_soft_prediction==true
    ov::Tensor feature_vector;
    friend std::ostream& operator<<(std::ostream& os, const ImageResultWithSoftPrediction& prediction) {
        os << static_cast<const ImageResult&>(prediction) << '[';
        for (int i = 0; i < prediction.soft_prediction.dims; ++i) {
            os << prediction.soft_prediction.size[i] << ',';
        }
        os << prediction.soft_prediction.channels() << "], [";
        if (prediction.saliency_map.data) {
            for (int i = 0; i < prediction.saliency_map.dims; ++i) {
                os << prediction.saliency_map.size[i] << ',';
            }
            os << prediction.saliency_map.channels() << "], ";
        } else {
            os << "0], ";
        }
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

    friend std::ostream& operator<<(std::ostream& os, const Contour& contour) {
        return os << contour.label << ": " << std::fixed << std::setprecision(3) << contour.probability << ", "
                  << contour.shape.size();
    }
};

static inline std::vector<Contour> getContours(const std::vector<SegmentedObject>& segmentedObjects) {
    std::vector<Contour> combined_contours;
    std::vector<std::vector<cv::Point>> contours;
    for (const SegmentedObject& obj : segmentedObjects) {
        cv::findContours(obj.mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE);
        // Assuming one contour output for findContours. Based on OTX this is a safe
        // assumption
        if (contours.size() != 1) {
            throw std::runtime_error("findContours() must have returned only one contour");
        }
        combined_contours.push_back({obj.label, obj.confidence, contours[0]});
    }
    return combined_contours;
}

struct HumanPose {
    std::vector<cv::Point2f> keypoints;
    float score;
};

struct HumanPoseResult : public ResultBase {
    HumanPoseResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<HumanPose> poses;
};

struct DetectedKeypoints {
    std::vector<cv::Point2f> keypoints;
    std::vector<float> scores;

    friend std::ostream& operator<<(std::ostream& os, const DetectedKeypoints& prediction) {
        float kp_x_sum = 0.f;
        for (const cv::Point2f& keypoint : prediction.keypoints) {
            kp_x_sum += keypoint.x;
        }
        os << "keypoints: (" << prediction.keypoints.size() << ", 2), keypoints_x_sum: ";
        os << std::fixed << std::setprecision(3) << kp_x_sum << ", scores: (" << prediction.scores.size() << ",)";
        return os;
    }

    explicit operator std::string() {
        std::stringstream ss;
        ss << *this;
        return ss.str();
    }
};

struct KeypointDetectionResult : public ResultBase {
    KeypointDetectionResult(int64_t frameId = -1, const std::shared_ptr<MetaData>& metaData = nullptr)
        : ResultBase(frameId, metaData) {}
    std::vector<DetectedKeypoints> poses;
};
