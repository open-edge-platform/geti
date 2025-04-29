# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from abc import ABC, abstractmethod

# noinspection PyPackageRequirements
import humps


class Randomizable(ABC):
    @classmethod
    @abstractmethod
    def randomize(cls, *args, **kwargs):
        raise NotImplementedError


class DictComparable:
    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class CamelJsonizable:
    # adds ability to convert inheriting class instance to/from camelCased JSON
    def to_json(self) -> dict:
        obj_dict = {}
        obj_int_dict = self.__dict__
        for k, v in obj_int_dict.items():
            if v is None:
                continue
            camelized_key = humps.camelize(k)
            if isinstance(v, CamelJsonizable):
                obj_dict[camelized_key] = v.to_json()
            else:
                obj_dict[camelized_key] = v
        return obj_dict

    @classmethod
    def from_json(cls, json_obj: dict):
        decamelized_keys_dict = {}
        for k, v in json_obj.items():
            snaked_key = humps.decamelize(k)
            decamelized_keys_dict[snaked_key] = v

        # noinspection PyArgumentList
        return cls(**decamelized_keys_dict)


class Meta(DictComparable, CamelJsonizable):
    def __init__(self, id="", created_at=None, created_by="", modified_at=None, modified_by=""):
        self.id = id
        self.created_at = created_at
        self.created_by = created_by
        self.modified_at = modified_at
        self.modified_by = modified_by
