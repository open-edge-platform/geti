# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from iai_core.entities.model import Model


def get_tiling_parameters(model: Model) -> dict:
    """
    Extracts the tiling parameters from the model.

    :param model: the model to extract the tiling parameters from
    :return: dictionary containing the tiling parameters
    """
    tiling_parameters = model.configuration.configurable_parameters.tiling_parameters  # type: ignore
    tiling_param_dict = {param: tiling_parameters.__dict__[param] for param in tiling_parameters.parameters}
    tiling_param_dict["enable_tile_classifier"] = tiling_param_dict.get("enable_tile_classifier", False)
    # Note: tile scaling is only configurable for instance segmentation models and is not present for detection
    tiling_param_dict["tile_ir_scale_factor"] = tiling_param_dict.get("tile_ir_scale_factor", 1.0)
    return tiling_param_dict


def get_tiler_configuration(tiling_parameters: dict) -> dict:
    """
    Extracts the tiling configuration needed for ModelAPI tilers from the model's configuration.
    Specifically, it extracts and calculates the following parameters:
        - tile_size: is multiplied 'tile_ir_scale_factor'
        - tiles_overlap: is divided by 'tile_ir_scale_factor'
        - max_pred_number: directly extracted as 'tile_max_number'

    Note: tiler configuration should only be manually set for legacy OTX models.

    :param tiling_parameters: dictionary containing the tiling parameters from which to extract the tiling parameters.
    :return: dictionary containing the tiling configuration for ModelAPI tiler.
    """
    try:
        tile_overlap = tiling_parameters["tile_overlap"]
        tile_max_number = tiling_parameters["tile_max_number"]
        tile_size = tiling_parameters["tile_size"]
        tile_ir_scale_factor = tiling_parameters["tile_ir_scale_factor"]
    except KeyError:
        raise ValueError
    return {
        "tile_size": int(tile_size * tile_ir_scale_factor),
        "tiles_overlap": tile_overlap / tile_ir_scale_factor,
        "max_pred_number": tile_max_number,
    }
