#
# Copyright (C) 2020-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#


class AsyncPipeline:
    def __init__(self, model):
        self.model = model
        self.model.load()

        self.completed_results = {}
        self.callback_exceptions = []
        self.model.inference_adapter.set_callback(self.callback)

    def callback(self, request, callback_args):
        try:
            id, meta, preprocessing_meta = callback_args
            self.completed_results[id] = (
                self.model.inference_adapter.copy_raw_result(request),
                meta,
                preprocessing_meta,
            )
        except Exception as e:  # noqa: BLE001 TODO: Figure out the exact exception that might be raised
            self.callback_exceptions.append(e)

    def submit_data(self, inputs, id, meta={}):
        self.model.perf.preprocess_time.update()
        inputs, preprocessing_meta = self.model.base_preprocess(inputs)
        self.model.perf.preprocess_time.update()

        self.model.perf.inference_time.update()
        callback_data = id, meta, preprocessing_meta
        self.model.infer_async_raw(inputs, callback_data)

    def get_raw_result(self, id):
        if id in self.completed_results:
            return self.completed_results.pop(id)
        return None

    def get_result(self, id):
        result = self.get_raw_result(id)
        if result:
            raw_result, meta, preprocess_meta = result
            self.model.perf.inference_time.update()

            self.model.perf.postprocess_time.update()
            result = (
                self.model.postprocess(raw_result, preprocess_meta),
                {
                    **meta,
                    **preprocess_meta,
                },
            )
            self.model.perf.postprocess_time.update()
            return result
        return None

    def is_ready(self):
        return self.model.is_ready()

    def await_all(self):
        if self.callback_exceptions:
            raise self.callback_exceptions[0]
        self.model.await_all()

    def await_any(self):
        if self.callback_exceptions:
            raise self.callback_exceptions[0]
        self.model.await_any()
