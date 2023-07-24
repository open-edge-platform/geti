"""
 Copyright (c) 2023 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import abc
import logging as log
from itertools import product

from openvino.model_api.models.types import NumericalValue
from openvino.model_api.pipelines import AsyncPipeline


class Tiler(metaclass=abc.ABCMeta):
    EXECUTION_MODES = ["async", "sync"]
    """
    An abstract tiler

    The abstract tiler is free from any executor dependencies.
    It sets the `Model` instance with the provided model
    and applys it to tiles of the input image, and then merges
    results from all tiles.

    The `_postprocess_tile` and `_merge_results` methods must be implemented in a specific inherited tiler.
    Attributes:
        logger (Logger): instance of the Logger
        model (Model): model being executed
        model_loaded (bool): a flag whether the model is loaded to device
        async_pipeline (AsyncPipeline): a pipeline for asynchronous execution mode
        execution_mode: Controls inference mode of the tiler (`async` or `sync`).
    """

    def __init__(self, model, configuration=dict(), execution_mode="async"):
        """
        Base constructor for creating a tiling pipeline

        Args:
            model: underlying model
            configuration: it contains values for parameters accepted by specific
              tiler (`tile_size`, `tiles_overlap` etc.) which are set as data attributes.
            execution_mode: Controls inference mode of the tiler (`async` or `sync`).
        """

        self.logger = log.getLogger()
        self.model = model
        for name, parameter in self.parameters().items():
            self.__setattr__(name, parameter.default_value)
        self._load_config(configuration)
        self.async_pipeline = AsyncPipeline(self.model)
        if execution_mode not in Tiler.EXECUTION_MODES:
            raise ValueError(
                f"Wrong execution mode. The following modes are supported {Tiler.EXECUTION_MODES}"
            )
        self.execution_mode = execution_mode

    def get_model(self):
        """Getter for underlying model"""
        return self.model

    @classmethod
    def parameters(cls):
        """Defines the description and type of configurable data parameters for the tiler.

        The structure is similar to model wrapper parameters.

        Returns:
            - the dictionary with defined wrapper tiler parameters
        """
        parameters = {}
        parameters.update(
            {
                "tile_size": NumericalValue(
                    value_type=int,
                    default_value=400,
                    min=1,
                    description="Size of one tile",
                ),
                "tiles_overlap": NumericalValue(
                    value_type=float,
                    default_value=0.5,
                    min=0.0,
                    max=1.0,
                    description="Overlap of tiles",
                ),
            }
        )
        return parameters

    def _load_config(self, config):
        """Reads the configuration and creates data attributes
           by setting the wrapper parameters with values from configuration.

        Args:
            config (dict): the dictionary with keys to be set as data attributes
              and its values. The example of the config is the following:
              {
                  'confidence_threshold': 0.5,
                  'resize_type': 'fit_to_window',
              }

        Note:
            The config keys should be provided in `parameters` method for each wrapper,
            then the default value of the parameter will be updated. If some key presented
            in the config is not introduced in `parameters`, it will be omitted.

         Raises:
            RuntimeError: if the configuration is incorrect
        """
        parameters = self.parameters()

        for name, param in parameters.items():
            try:
                value = param.from_str(
                    self.model.inference_adapter.get_rt_info(
                        ["model_info", name]
                    ).astype(str)
                )
                self.__setattr__(name, value)
            except RuntimeError as error:
                missing_rt_info = (
                    "Cannot get runtime attribute. Path to runtime attribute is incorrect."
                    in str(error)
                )
                is_OVMSAdapter = (
                    str(error) == "OVMSAdapter does not support RT info getting"
                )
                if not missing_rt_info and not is_OVMSAdapter:
                    raise

        for name, value in config.items():
            if value is None:
                continue
            if name in parameters:
                errors = parameters[name].validate(value)
                if errors:
                    self.logger.error(f'Error with "{name}" parameter:')
                    for error in errors:
                        self.logger.error(f"\t{error}")
                    raise RuntimeError("Incorrect user configuration")
                value = parameters[name].get_value(value)
                self.__setattr__(name, value)
            else:
                self.logger.warning(
                    f'The parameter "{name}" not found in tiler, will be omitted'
                )

    def __call__(self, inputs):
        """
        Applies full pipeline of tiling inference in one call.

        Args:
            inputs: raw input data, the data type is defined by underlying model wrapper

        Returns:
            - postprocessed data in the format defined by underlying model wrapper
        """

        tile_coords = self._tile(inputs)
        tile_coords = self._filter_tiles(inputs, tile_coords)

        if self.execution_mode == "sync":
            return self._predict_sync(inputs, tile_coords)
        return self._predict_async(inputs, tile_coords)

    def _tile(self, image):
        """Tiles an input image to overlapping or non-overlapping patches.

        This method implementation also adds the full image as the first tile to process.

        Args:
            image: Input image to tile.

        Returns:
            Tiles coordinates
        """
        height, width = image.shape[:2]

        coords = [[0, 0, width, height]]
        for loc_j, loc_i in product(
            range(0, width, int(self.tile_size * (1 - self.tiles_overlap))),
            range(0, height, int(self.tile_size * (1 - self.tiles_overlap))),
        ):
            x2 = min(loc_j + self.tile_size, width)
            y2 = min(loc_i + self.tile_size, height)
            coords.append([loc_j, loc_i, x2, y2])

        return coords

    def _filter_tiles(self, image, tile_coords):
        """Filter tiles by some criterion

        Args:
            image: full size image
            tile_coords: tile coordinates

        Returns:
            keep_coords: tile coordinates to keep
        """
        return tile_coords

    def _predict_sync(self, image, tile_coords):
        """Makes prediction by splitting the input image into tiles in synchronous mode.

        Args:
            image: full size image
            tile_coords: list of tile coordinates

        Returns:
            Inference results aggregated from all tiles
        """
        tile_results = []
        for coord in tile_coords:
            tile_img = self._crop_tile(image, coord)
            tile_predictions = self.model(tile_img)
            tile_result = self._postprocess_tile(tile_predictions, coord)
            tile_results.append(tile_result)

        return self._merge_results(tile_results, image.shape)

    def _predict_async(self, image, tile_coords):
        """Makes prediction by splitting the input image into tiles in asynchronous mode.

        Args:
            image: full size image
            tile_coords: tile coordinates

        Returns:
            Inference results aggregated from all tiles
        """
        for i, coord in enumerate(tile_coords):
            self.async_pipeline.submit_data(self._crop_tile(image, coord), i)
        self.async_pipeline.await_all()

        num_tiles = len(tile_coords)
        tile_results = []
        for j in range(num_tiles):
            tile_prediction, _ = self.async_pipeline.get_result(j)
            tile_result = self._postprocess_tile(tile_prediction, tile_coords[j])
            tile_results.append(tile_result)

        return self._merge_results(tile_results, image.shape)

    @abc.abstractmethod
    def _postprocess_tile(self, predictions, coord):
        """Postprocesses predicitons made by a model from one tile.

        Args:
            predictions: model-dependent set of predicitons or one prediciton
            coord: a list containing coordinates for the processed tile

        Returns:
            Postprocessed predictions
        """

    @abc.abstractmethod
    def _merge_results(self, results, shape):
        """Merge results from all tiles.

        Args:
            results: list of tile results
            shape: original full-res image shape
        """

    def _crop_tile(self, image, coord):
        """Crop tile from the full image.

        Args:
            image: full-res image
            coord: tile coordinates

        Returns:
            cropped tile
        """
        x1, y1, x2, y2 = coord
        return image[y1:y2, x1:x2]
