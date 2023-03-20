#include "models/detection_model_ext.h"

#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "models/image_model.h"
#include "models/input_data.h"
#include "models/results.h"

DetectionModelExt::DetectionModelExt(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : DetectionModel(model, configuration) {
    auto iou_t_iter = configuration.find("iou_t");
    if (iou_t_iter != configuration.end()) {
        boxIOUThreshold = iou_t_iter->second.as<float>();
    } else {
        if (model->has_rt_info<std::string>("model_info", "iou_t")) {
            boxIOUThreshold = model->get_rt_info<float>("model_info", "iou_t");
        }
    }
}

DetectionModelExt::DetectionModelExt(std::shared_ptr<InferenceAdapter>& adapter)
    : DetectionModel(adapter) {
    auto configuration = adapter->getModelConfig();
    auto iou_t_iter = configuration.find("iou_t");
    if (iou_t_iter != configuration.end()) {
        boxIOUThreshold = iou_t_iter->second.as<float>();
    }
}
