# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from iai_core.entities.label import Domain, Label
from iai_core.entities.scored_label import LabelSource, ScoredLabel

from geti_types import ID


class TestScoredLabel:
    def test_scored_label(self):
        """
        <b>Description:</b>
        Check the ScoredLabel can correctly return the value

        <b>Input data:</b>
        Label

        <b>Expected results:</b>
        Test passes if the results match
        """
        car = Label(name="car", domain=Domain.DETECTION, is_empty=False, id_=ID(123456789))
        person = Label(name="person", domain=Domain.DETECTION, is_empty=False, id_=ID(987654321))
        car_label = ScoredLabel(label_id=car.id_, is_empty=car.is_empty)
        person_label = ScoredLabel(label_id=person.id_, is_empty=person.is_empty)

        for attr in ["id_", "is_empty"]:
            assert getattr(car_label, attr) == getattr(car, attr)

        assert car_label != car
        assert car_label != person_label
        assert hash(car_label) == hash(str(car_label))

        probability = 0.0
        assert car_label.probability == probability
        delta_probability = 0.4
        probability += delta_probability
        car_label.probability += delta_probability
        assert car_label.probability == probability

        label_source = LabelSource()
        assert car_label.label_source == label_source
        user_name = "User Name"
        car_label.label_source.user_id = user_name
        label_source_with_user = LabelSource(user_id=user_name)
        assert car_label.label_source == label_source_with_user
