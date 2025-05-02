# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from iai_core_py.configuration.elements.default_model_parameters import DefaultModelParameters


class TestModelConfiguration:
    def test_model_configuration(self):
        mc = DefaultModelParameters()
        assert hasattr(mc, "learning_parameters")

        epoch_default = mc.learning_parameters.get_metadata("epochs")["default_value"]
        batch_size_default = mc.learning_parameters.get_metadata("batch_size")["default_value"]

        assert mc.learning_parameters.epochs == epoch_default
        assert mc.learning_parameters.batch_size == batch_size_default

        mc.learning_parameters.epochs = epoch_default + 5
        mc.learning_parameters.batch_size = batch_size_default + 4

        assert mc.learning_parameters.batch_size == batch_size_default + 4
        assert mc.learning_parameters.epochs == epoch_default + 5
