# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from zipfile import ZipFile

import pytest
from bson import ObjectId, UuidRepresentation
from bson.json_util import JSONOptions, dumps, loads
from sc_sdk.repos.mappers import MediaIdentifierToMongo

from job.usecases import ExportDataRedactionUseCase, ImportDataRedactionUseCase
from job.usecases.data_redaction_usecase import BaseDataRedactionUseCase, get_random_objectid_between_dates


@pytest.mark.ProjectIEMsComponent
class TestBaseDataRedactionUseCase:
    def test_is_file_label_schema_json(self) -> None:
        assert not BaseDataRedactionUseCase._is_file_label_schema_json("random_string")
        assert BaseDataRedactionUseCase._is_file_label_schema_json("label_schema_0d032323-336c-4881-be5c.json")
        assert BaseDataRedactionUseCase._is_file_label_schema_json("label-schema_c956aabe-a927-44bc-9588.json")

    def test_is_file_model_xml(self) -> None:
        assert not BaseDataRedactionUseCase._is_file_model_xml("random_string")
        assert BaseDataRedactionUseCase._is_file_model_xml("openvino_166c6196-bf25-44d0-b6bf-d398e4189b3c.xml")
        assert BaseDataRedactionUseCase._is_file_model_xml("model_fp16_non-xai_8619c552-5c5d-4095-9012.xml")

    def test_is_file_exportable_code(self) -> None:
        assert not BaseDataRedactionUseCase._is_file_exportable_code("random_string")
        assert BaseDataRedactionUseCase._is_file_exportable_code("exportable_code_4cd35fb9-6a7b-430f-81a3.whl")
        assert BaseDataRedactionUseCase._is_file_exportable_code("exportable-code_fp16_non-xai_e95289a4-ce68-4e6b.whl")

    def test_is_file_reference_features_json(self) -> None:
        assert not BaseDataRedactionUseCase._is_file_reference_features_json("random_string")
        assert BaseDataRedactionUseCase._is_file_reference_features_json(
            "reference_features_0d032323-336c-4881-be5c.json"
        )


@pytest.mark.ProjectIEMsComponent
class TestExportDataRedactionUseCase:
    def test_get_random_objectid_between_dates(self) -> None:
        min_date = datetime(1983, 3, 4, tzinfo=timezone.utc)
        max_date = datetime(1983, 3, 5, tzinfo=timezone.utc)
        min_date_epoch = int(min_date.timestamp())
        max_date_epoch = int(max_date.timestamp())

        random_oid = get_random_objectid_between_dates(min_date, max_date)

        assert isinstance(random_oid, ObjectId)
        random_oid_int = int(str(random_oid), 16)
        random_oid_epoch = random_oid_int // 2**64  # extract the timestamp component by stripping the lowest 8 bytes
        assert min_date_epoch <= random_oid_epoch <= max_date_epoch

    def test_replace_objectid_in_mongodb_doc(self, fxt_mongo_id) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc_1 = {
            "_id": ObjectId(fxt_mongo_id(2)),
            "str_field": "hello",
            "int_field": 15,
            "some_id": ObjectId(fxt_mongo_id(3)),
        }
        doc_2 = {
            "_id": ObjectId(fxt_mongo_id(1)),
            "str_field": "hello",
            "int_field": 15,
            "some_id": ObjectId(fxt_mongo_id(4)),
        }
        bson_doc_1, bson_doc_2 = dumps(doc_1), dumps(doc_2)

        out_bson_doc_1 = data_redaction_use_case.replace_objectid_in_mongodb_doc(bson_doc=bson_doc_1)
        out_bson_doc_2 = data_redaction_use_case.replace_objectid_in_mongodb_doc(bson_doc=bson_doc_2)

        out_doc_1, out_doc_2 = loads(out_bson_doc_1), loads(out_bson_doc_2)
        assert isinstance(out_doc_1["_id"], dict)
        assert "$sid" in out_doc_1["_id"]
        assert isinstance(out_doc_1["some_id"], dict)
        assert "$sid" in out_doc_1["some_id"]
        assert data_redaction_use_case.objectid_replacement_min_int == int(out_doc_2["_id"]["$sid"], 16)

    def test_replace_media_based_objectid_in_mongodb_doc(self, fxt_ote_id) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc = {
            "_id": ObjectId(fxt_ote_id(1)),
            "foo": "bar",
            "media_identifier": {
                "type": "video_frame",
                "media_id": ObjectId(fxt_ote_id(2)),
                "frame_index": 10,
            },
        }

        out_doc = data_redaction_use_case.replace_media_based_objectid_in_mongodb_doc(doc)

        assert out_doc["_id"] != ObjectId(fxt_ote_id(1))
        assert out_doc["foo"] == "bar"
        assert "media_identifier" in out_doc

    def test_replace_empty_objectid_in_mongodb_doc(self, fxt_ote_id) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc = {
            "_id": ObjectId(fxt_ote_id(1)),
            "ground_truth_dataset_id": "",
            "model_id": ObjectId(fxt_ote_id(2)),
            "name": "Model test",
            "state": "FAILED",
        }
        bson_doc = dumps(doc)

        out_bson_doc = data_redaction_use_case.replace_objectid_in_mongodb_doc(bson_doc=bson_doc)

        out_doc = loads(out_bson_doc)
        assert out_doc["_id"] != ObjectId(fxt_ote_id(1))
        assert out_doc["ground_truth_dataset_id"] == ""
        assert out_doc["model_id"] != ObjectId(fxt_ote_id(2))
        assert out_doc["state"] == "FAILED"

    def test_remove_job_id_in_mongodb_doc(self, fxt_ote_id) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc = {
            "_id": ObjectId(fxt_ote_id(1)),
            "foo": "bar",
            "job_id": ObjectId(fxt_ote_id(2)),
        }
        expected_out_doc = {
            "_id": ObjectId(fxt_ote_id(1)),
            "foo": "bar",
        }

        out_doc = data_redaction_use_case.remove_job_id_in_mongodb_doc(doc)

        assert out_doc == expected_out_doc

    def test_replace_objectid_in_url(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        original_url = "/dataset_storages/659bb165c7d3a5f9a02be30a/659bb180c7d3a5f9a02be30b_thumbnail.jpg"

        out_url = data_redaction_use_case.replace_objectid_in_url(url=original_url)

        assert len(out_url) == len(original_url)
        assert out_url.endswith("_thumbnail.jpg")
        assert "/dataset_storages/" in out_url
        assert "659bb165c7d3a5f9a02be30a" not in out_url
        assert "659bb180c7d3a5f9a02be30b" not in out_url

    def test_replace_objectid_based_binary_filename_in_mongodb_doc(self, fxt_mongo_id) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc_1 = {
            "_id": ObjectId(fxt_mongo_id(1)),
            "str_field": "hello",
            "int_field": 15,
            "binary_filename": f"{str(fxt_mongo_id(1))}.jpg",
        }
        doc_2 = {
            "_id": ObjectId(fxt_mongo_id(2)),
            "str_field": "hello",
            "int_field": 15,
            "binary_filename": f"{str(fxt_mongo_id(2))}.mp4",
        }
        doc_3 = {
            "_id": ObjectId(fxt_mongo_id(3)),
            "str_field": "hello",
            "int_field": 15,
            "binary_filename": "cat_video.mp4",
        }
        bson_doc_1, bson_doc_2, bson_doc_3 = dumps(doc_1), dumps(doc_2), dumps(doc_3)

        out_bson_doc_1 = data_redaction_use_case.replace_objectid_based_binary_filename_in_mongodb_doc(bson_doc_1)
        out_bson_doc_2 = data_redaction_use_case.replace_objectid_based_binary_filename_in_mongodb_doc(bson_doc_2)
        out_bson_doc_3 = data_redaction_use_case.replace_objectid_based_binary_filename_in_mongodb_doc(bson_doc_3)

        out_doc_1, out_doc_2, out_doc_3 = loads(out_bson_doc_1), loads(out_bson_doc_2), loads(out_bson_doc_3)
        assert ObjectId.is_valid(out_doc_1["_id"])
        assert out_doc_1["binary_filename"].endswith(".jpg")
        assert ObjectId.is_valid(out_doc_1["binary_filename"].removesuffix(".jpg"))
        assert ObjectId.is_valid(out_doc_2["_id"])
        assert out_doc_2["binary_filename"].endswith(".mp4")
        assert ObjectId.is_valid(out_doc_2["binary_filename"].removesuffix(".mp4"))
        assert ObjectId.is_valid(out_doc_3["_id"])
        assert out_doc_3["binary_filename"] == "cat_video.mp4"
        # Verify the consistency with _id
        out_bson_doc_1 = data_redaction_use_case.replace_objectid_in_mongodb_doc(out_bson_doc_1)
        out_doc_1 = loads(out_bson_doc_1)
        assert out_doc_1["binary_filename"] == out_doc_1["_id"]["$sid"] + ".jpg"

    def test_replace_objectid_in_config_json(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        config_data_json: dict = {
            "key1": {
                "key1.1": "val1.1",
            },
            "key2": [
                {
                    "_id": "65ef06f6a57888e625447b6c",
                    "key2.1": [
                        "65ef06f6a57888e625447b66",
                        "65ef06f6a57888e625447b67",
                        "65ef06f6a57888e625447b68",
                        "65ef06f6a57888e625447b69",
                    ],
                    "key2.2": "65ef06f6a57888e625447b70 65ef06f6a57888e625447b71",
                }
            ],
        }
        config_data = json.dumps(config_data_json)

        redacted_data = data_redaction_use_case.replace_objectid_in_config_json(config_data=config_data)

        redacted_data_json = json.loads(redacted_data)
        assert redacted_data_json["key1"] == config_data_json["key1"]
        assert redacted_data_json["key2"][0]["_id"] != config_data_json["key2"][0]["_id"]
        assert ObjectId.is_valid(redacted_data_json["key2"][0]["_id"])
        assert redacted_data_json["key2"][0]["key2.1"] != config_data_json["key2"][0]["key2.1"]
        assert redacted_data_json["key2"][0]["key2.2"] != config_data_json["key2"][0]["key2.2"]
        assert len(redacted_data_json["key2"][0]["key2.1"]) == 4
        assert len(redacted_data_json["key2"][0]["key2.2"].split()) == 2
        assert all(ObjectId.is_valid(id_) for id_ in redacted_data_json["key2"][0]["key2.1"])
        assert all(ObjectId.is_valid(id_) for id_ in redacted_data_json["key2"][0]["key2.2"].split())

    def test_replace_objectid_in_reference_features_json(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        reference_features_json: list[dict] = [
            {
                "label_id": "65ef06f6a57888e625447b66",
                "name": "A",
                "color": "#FF0000",
                "numpy_filename": "reference_feature_65ef06f6a57888e625447b66.npz",
            },
            {
                "label_id": "65ef06f6a57888e625447b67",
                "name": "B",
                "color": "#FF0002",
                "numpy_filename": "reference_feature_65ef06f6a57888e625447b67.npz",
            },
        ]
        config_data = json.dumps(reference_features_json)

        redacted_data = data_redaction_use_case.replace_objectid_in_config_json(config_data=config_data)

        redacted_data_json = json.loads(redacted_data)
        assert redacted_data_json[0]["name"] == reference_features_json[0]["name"]
        assert redacted_data_json[0]["color"] == reference_features_json[0]["color"]
        assert redacted_data_json[1]["name"] == reference_features_json[1]["name"]
        assert redacted_data_json[1]["color"] == reference_features_json[1]["color"]
        assert redacted_data_json[0]["label_id"] != reference_features_json[0]["label_id"]
        assert redacted_data_json[1]["label_id"] != reference_features_json[1]["label_id"]
        assert redacted_data_json[0]["numpy_filename"] != reference_features_json[0]["numpy_filename"]
        assert redacted_data_json[1]["numpy_filename"] != reference_features_json[1]["numpy_filename"]
        assert ObjectId.is_valid(redacted_data_json[0]["label_id"])
        assert ObjectId.is_valid(redacted_data_json[1]["label_id"])
        assert ObjectId.is_valid(redacted_data_json[0]["numpy_filename"].removesuffix(".npz").split("_")[-1])
        assert ObjectId.is_valid(redacted_data_json[1]["numpy_filename"].removesuffix(".npz").split("_")[-1])

    def test_remove_objectid_from_model_xml(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        model_xml_data: str = """<?xml version="1.0"?>
<net name="torch_jit" version="11">
    <layers>
        <layer id="0" name="data" type="Parameter" version="opset1">
            <data shape="1,3,224,224" element_type="f32" />
            <output>
                <port id="0" precision="FP32" names="data">
                    <dim>1</dim>
                    <dim>3</dim>
                    <dim>224</dim>
                    <dim>224</dim>
                </port>
            </output>
        </layer>
    </layers>
    <edges>
        <edge from-layer="0" from-port="0" to-layer="3" to-port="0" />
    </edges>
    <rt_info>
        <Runtime_version value="2024.3.0-16041-1e3b88e4e3f-releases/2024/3" />
        <conversion_parameters>
            <framework value="pytorch" />
            <is_python_object value="True" />
        </conversion_parameters>
        <model_info>
            <blur_strength value="-1" />
            <label_ids value="background 66d68ff612144f0f3afa513d 66d68ff612144f0f3afa513e 66d68ff612144f0f3afa513f" />
            <label_info value="{&quot;label_names&quot;: [&quot;background&quot;, &quot;66d68ff612144f0f3afa513d&quot;, &quot;66d68ff612144f0f3afa513e&quot;, &quot;66d68ff612144f0f3afa513f&quot;], &quot;label_groups&quot;: [[&quot;background&quot;, &quot;66d68ff612144f0f3afa513d&quot;, &quot;66d68ff612144f0f3afa513e&quot;, &quot;66d68ff612144f0f3afa513f&quot;]], &quot;ignore_index&quot;: 255}" />
            <labels value="background 66d68ff612144f0f3afa513d 66d68ff612144f0f3afa513e 66d68ff612144f0f3afa513f" />
            <mean_values value="123.675 116.28 103.53" />
            <model_type value="Segmentation" />
            <optimization_config value="{&quot;advanced_parameters&quot;: {&quot;activations_range_estimator_params&quot;: {&quot;min&quot;: {&quot;statistics_type&quot;: &quot;QUANTILE&quot;, &quot;aggregator_type&quot;: &quot;MIN&quot;, &quot;quantile_outlier_prob&quot;: 0.0001}, &quot;max&quot;: {&quot;statistics_type&quot;: &quot;QUANTILE&quot;, &quot;aggregator_type&quot;: &quot;MAX&quot;, &quot;quantile_outlier_prob&quot;: 0.0001}}}}" />
            <pad_value value="0" />
            <resize_type value="standard" />
            <return_soft_prediction value="True" />
            <reverse_input_channels value="False" />
            <scale_values value="58.395 57.12 57.375" />
            <soft_threshold value="0.5" />
            <task_type value="segmentation" />
        </model_info>
    </rt_info>
</net>"""  # noqa: E501
        label_ids_xml_regex = r'<label_ids value=".*[0-9a-fA-F]{24}.*" />'
        label_ids_before_redaction = re.search(label_ids_xml_regex, model_xml_data)
        assert label_ids_before_redaction is not None, "Input data and/or regex are incorrectly built"
        labels_xml_regex = r'<labels value=".*[0-9a-fA-F]{24}.*" />'
        labels_before_redaction = re.search(labels_xml_regex, model_xml_data)
        assert labels_before_redaction is not None, "Input data and/or regex are incorrectly built"
        label_info_xml_regex = r'<label_info value=".*[0-9a-fA-F]{24}.*" />'
        label_info_before_redaction = re.search(label_info_xml_regex, model_xml_data)
        assert label_info_before_redaction is not None, "Input data and/or regex are incorrectly built"

        redacted_data = data_redaction_use_case.replace_objectid_in_model_xml(model_xml_data=model_xml_data)

        redacted_data_str = redacted_data.decode("utf-8")
        assert "<?xml version" in redacted_data_str
        assert "<rt_info>" in redacted_data_str
        assert "<model_info>" in redacted_data_str
        label_ids_after_redaction = re.search(label_ids_xml_regex, redacted_data_str)
        assert label_ids_after_redaction is not None, "'label_ids' not found after redaction"
        assert label_ids_after_redaction.group() != label_ids_before_redaction.group(), "'label_ids' did not change"
        labels_after_redaction = re.search(labels_xml_regex, redacted_data_str)
        assert labels_after_redaction is not None, "'labels' not found after redaction"
        assert labels_after_redaction.group() != labels_before_redaction.group(), "'labels' did not change"
        label_info_after_redaction = re.search(label_info_xml_regex, redacted_data_str)
        assert label_info_after_redaction is not None, "'label_info' not found after redaction"
        assert label_info_after_redaction.group() != label_info_before_redaction.group(), "'label_info' did not change"

    def test_replace_objectid_in_exportable_code_wheel(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        # Create a .whl with similar structure of exportable code
        whl_files = [
            "model/model.xml",
            "model/model.bin",
            "model/config.json",
            "python/requirements.txt",
            "python/LICENSE",
            "python/demo.py",
            "README.md",
        ]
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            tempfile.NamedTemporaryFile(suffix=".whl", delete=False) as temp_zip,
            ZipFile(temp_zip.name, "w") as zipf,
        ):
            for arc_path in whl_files:
                fs_path = os.path.join(temp_dir, arc_path)
                os.makedirs(os.path.dirname(fs_path), exist_ok=True)
                with open(fs_path, "w") as fp:
                    fp.write("original_data")
                zipf.write(fs_path, arcname=arc_path)

        with (
            patch.object(
                data_redaction_use_case, "replace_objectid_in_config_json", return_value="redacted_data"
            ) as mock_redact_json,
            patch.object(
                data_redaction_use_case, "replace_objectid_in_model_xml", return_value="redacted_data"
            ) as mock_redact_xml,
        ):
            data_redaction_use_case.replace_objectid_in_exportable_code_wheel(temp_zip.name)

        # Verify that the .xml and config.json where identified and redacted
        mock_redact_xml.assert_called_once_with("original_data")
        mock_redact_json.assert_called_once_with("original_data")
        # Verify that the output whl contains the same files as the original one
        with ZipFile(temp_zip.name, "r") as out_zipf:
            redacted_whl_files = [item.filename for item in out_zipf.infolist()]
        assert sorted(redacted_whl_files) == sorted(whl_files)

    @pytest.mark.parametrize(
        "file_path,is_model_xml,is_json_config,is_exportable_code",
        [
            ("weights_033d48b2-7fb0-4120-9816-1c21da956e4d.pth", False, False, False),
            ("openvino_91b5b988-e41d-47ff-962f-4b6cd0ff2d30.xml", True, False, False),
            ("label_schema_41f4b824-3b6c-4411-abd7-d9992044d213.json", False, True, False),
            ("reference_features_96f5a896-4fa7-4721-91ca-74dfae66f5df.json", False, True, False),
            ("exportable_code_56734cb5-a6aa-4179-963e-2df288e77d57.whl", False, False, True),
        ],
        ids=[
            "regular file",
            "model xml",
            "label schema json",
            "reference features json",
            "exportable code wheel",
        ],
    )
    def test_replace_objectid_in_file(self, file_path, is_model_xml, is_json_config, is_exportable_code) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.object(
                data_redaction_use_case, "replace_objectid_in_config_json", return_value="redacted_data"
            ) as mock_redact_json,
            patch.object(
                data_redaction_use_case, "replace_objectid_in_model_xml", return_value=b"redacted_data"
            ) as mock_redact_xml,
            patch.object(
                data_redaction_use_case, "replace_objectid_in_exportable_code_wheel", return_value="redacted_data"
            ) as mock_redact_whl,
        ):
            # Create the file
            file_path = os.path.join(temp_dir, file_path)
            with open(file_path, "w") as fp:
                fp.write("test_data")

            out_file_path = data_redaction_use_case.replace_objectid_in_file(file_path)

        mock_redact_xml.assert_called() if is_model_xml else mock_redact_xml.assert_not_called()
        mock_redact_json.assert_called() if is_json_config else mock_redact_json.assert_not_called()
        mock_redact_whl.assert_called() if is_exportable_code else mock_redact_whl.assert_not_called()
        assert out_file_path == file_path

    def test_mask_user_info_in_mongodb_doc(self, fxt_mongo_id) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc = {
            "_id": ObjectId(fxt_mongo_id(1)),
            "user_id": "1234",  # as literal string, without any suffix
            "author": uuid.uuid4(),  # as uuid, without '_id' suffix
            "editor_name": uuid.uuid4(),  # as uuid, with '_name' suffix
            "some_id": ObjectId(fxt_mongo_id(2)),
            "user_uid": uuid.uuid4(),
        }
        json_options = JSONOptions(uuid_representation=UuidRepresentation.STANDARD)
        bson_doc = dumps(doc, json_options=json_options)

        out_bson_doc = data_redaction_use_case.mask_user_info_in_mongodb_doc(bson_doc)

        out_doc = loads(out_bson_doc)
        # Check that the expected fields are redacted
        assert out_doc["user_id"] == "$user_id_str"
        assert out_doc["author"] == "$user_id_uuid4"
        assert out_doc["editor_name"] == "$user_id_uuid4"
        assert out_doc["user_uid"] == "$user_id_uuid4"
        # Check that the other fields are unchanged
        assert out_doc["_id"] == doc["_id"]
        assert out_doc["some_id"] == doc["some_id"]

    def test_remove_container_info_in_mongodb_doc(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc = {
            "foo": "bar",
            "organization_id": "value1",
            "workspace_id": "value2",
            "project_id": "value3",
            "location": "value4",
        }

        out_doc = data_redaction_use_case.remove_container_info_in_mongodb_doc(doc=doc)

        assert out_doc == {"foo": "bar"}

    def test_remove_lock_in_mongodb_doc(self) -> None:
        data_redaction_use_case = ExportDataRedactionUseCase()
        doc = {
            "foo": "bar",
            "locked_until.user1": "some_date",
        }

        out_doc = data_redaction_use_case.remove_lock_in_mongodb_doc(doc=doc)

        assert out_doc == {"foo": "bar"}


class TestImportDataRedactionUseCase:
    def test_recreate_objectid_in_mongodb_doc(self, fxt_mongo_id) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase(objectid_replacement_min_int=0)
        bson_doc = (
            '{"_id": {"$sid": "30c98a73d5f1fb7e6e3c1a51"}, "str_field": "hello", '
            '"int_field": 15, "some_id": {"$sid": "30c98a73d5f1fb7e6e3c1a52"}}'
        )

        out_bson_doc = data_redaction_use_case.recreate_objectid_in_mongodb_doc(bson_doc=bson_doc)

        out_doc = loads(out_bson_doc)
        assert isinstance(out_doc["_id"], ObjectId)
        assert isinstance(out_doc["some_id"], ObjectId)
        assert int(str(out_doc["some_id"]), 16) - int(str(out_doc["_id"]), 16) == 1

    def test_recreate_media_based_objectid_in_mongodb_doc(self, fxt_ote_id) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase()
        doc = {
            "_id": ObjectId(fxt_ote_id(1)),
            "foo": "bar",
            "media_identifier": {
                "type": "video_frame",
                "media_id": ObjectId(fxt_ote_id(2)),
                "frame_index": 10,
            },
        }
        media_identifier = MediaIdentifierToMongo.backward(doc["media_identifier"])

        out_doc = data_redaction_use_case.recreate_media_based_objectid_in_mongodb_doc(doc)

        assert out_doc["_id"] == ObjectId(str(media_identifier.as_id()))
        assert out_doc["foo"] == "bar"
        assert "media_identifier" in out_doc

    def test_recreate_objectid_in_url(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase(objectid_replacement_min_int=0)
        original_url = "/dataset_storages/659bb165c7d3a5f9a02be30a/659bb180c7d3a5f9a02be30b_thumbnail.jpg"

        out_url = data_redaction_use_case.recreate_objectid_in_url(url=original_url)

        assert len(out_url) == len(original_url)
        assert out_url.endswith("_thumbnail.jpg")
        assert "/dataset_storages/" in out_url
        assert "659bb165c7d3a5f9a02be30a" not in out_url
        assert "659bb180c7d3a5f9a02be30b" not in out_url

    def test_recreate_objectid_based_binary_filename_in_mongodb_doc(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase(objectid_replacement_min_int=0)
        bson_doc = (
            '{"_id": {"$sid": "65ba05b6dd99642320a51c49"}, "str_field": "hello", '
            '"int_field": 15, "binary_filename": "65ba05b6dd99642320a51c49.mp4"}'
        )
        bson_doc = data_redaction_use_case.recreate_objectid_in_mongodb_doc(bson_doc)

        out_bson_doc = data_redaction_use_case.recreate_objectid_based_binary_filename_in_mongodb_doc(bson_doc)

        out_doc = loads(out_bson_doc)
        assert isinstance(out_doc["_id"], ObjectId)
        # Verify the consistency with _id
        assert out_doc["binary_filename"] == f"{str(out_doc['_id'])}.mp4"

    def test_recreate_objectid_in_config_json(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase(objectid_replacement_min_int=0)
        config_data_json: dict = {
            "key1": {
                "key1.1": "val1.1",
            },
            "key2": [
                {
                    "_id": "30c98a73d5f1fb7e6e3c1a52",
                    "key2.1": [
                        "30c98a73d5f1fb7e6e3c1a53",
                        "30c98a73d5f1fb7e6e3c1a54",
                        "30c98a73d5f1fb7e6e3c1a55",
                        "30c98a73d5f1fb7e6e3c1a56",
                    ],
                    "key2.2": "30c98a73d5f1fb7e6e3c1a57 30c98a73d5f1fb7e6e3c1a58",
                }
            ],
        }
        config_data = json.dumps(config_data_json)

        redacted_data = data_redaction_use_case.recreate_objectid_in_config_json(config_data=config_data)

        redacted_data_json = json.loads(redacted_data)
        assert redacted_data_json["key1"] == config_data_json["key1"]
        assert redacted_data_json["key2"][0]["_id"] != config_data_json["key2"][0]["_id"]
        assert ObjectId.is_valid(redacted_data_json["key2"][0]["_id"])
        assert redacted_data_json["key2"][0]["key2.1"] != config_data_json["key2"][0]["key2.1"]
        assert len(redacted_data_json["key2"][0]["key2.1"]) == 4
        assert len(redacted_data_json["key2"][0]["key2.2"].split()) == 2
        assert all(ObjectId.is_valid(id_) for id_ in redacted_data_json["key2"][0]["key2.1"])
        assert all(ObjectId.is_valid(id_) for id_ in redacted_data_json["key2"][0]["key2.2"].split())

    def test_recreate_objectid_in_reference_features_json(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase(objectid_replacement_min_int=0)
        reference_features_json: list[dict] = [
            {
                "label_id": "30c98a73d5f1fb7e6e3c1a52",
                "name": "A",
                "color": "#FF0000",
                "numpy_filename": "reference_feature_30c98a73d5f1fb7e6e3c1a52.npz",
            },
            {
                "label_id": "30c98a73d5f1fb7e6e3c1a53",
                "name": "B",
                "color": "#FF0002",
                "numpy_filename": "reference_feature_30c98a73d5f1fb7e6e3c1a53.npz",
            },
        ]
        config_data = json.dumps(reference_features_json)

        redacted_data = data_redaction_use_case.recreate_objectid_in_config_json(config_data=config_data)

        redacted_data_json = json.loads(redacted_data)
        assert redacted_data_json[0]["name"] == reference_features_json[0]["name"]
        assert redacted_data_json[0]["color"] == reference_features_json[0]["color"]
        assert redacted_data_json[1]["name"] == reference_features_json[1]["name"]
        assert redacted_data_json[1]["color"] == reference_features_json[1]["color"]
        assert redacted_data_json[0]["label_id"] != reference_features_json[0]["label_id"]
        assert redacted_data_json[1]["label_id"] != reference_features_json[1]["label_id"]
        assert redacted_data_json[0]["numpy_filename"] != reference_features_json[0]["numpy_filename"]
        assert redacted_data_json[1]["numpy_filename"] != reference_features_json[1]["numpy_filename"]
        assert ObjectId.is_valid(redacted_data_json[0]["label_id"])
        assert ObjectId.is_valid(redacted_data_json[1]["label_id"])
        assert ObjectId.is_valid(redacted_data_json[0]["numpy_filename"].removesuffix(".npz").split("_")[-1])
        assert ObjectId.is_valid(redacted_data_json[1]["numpy_filename"].removesuffix(".npz").split("_")[-1])

    def test_recreate_objectid_from_model_xml(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase(objectid_replacement_min_int=0)
        model_xml_data: str = """<?xml version="1.0"?>
<net name="torch_jit" version="11">
    <layers>
        <layer id="0" name="data" type="Parameter" version="opset1">
            <data shape="1,3,224,224" element_type="f32" />
            <output>
                <port id="0" precision="FP32" names="data">
                    <dim>1</dim>
                    <dim>3</dim>
                    <dim>224</dim>
                    <dim>224</dim>
                </port>
            </output>
        </layer>
    </layers>
    <edges>
        <edge from-layer="0" from-port="0" to-layer="3" to-port="0" />
    </edges>
    <rt_info>
        <Runtime_version value="2024.3.0-16041-1e3b88e4e3f-releases/2024/3" />
        <conversion_parameters>
            <framework value="pytorch" />
            <is_python_object value="True" />
        </conversion_parameters>
        <model_info>
            <blur_strength value="-1" />
            <label_ids value="background 30c98a73d5f1fb7e6e3c1a52 30c98a73d5f1fb7e6e3c1a53 30c98a73d5f1fb7e6e3c1a54" />
            <label_info value="{&quot;label_names&quot;: [&quot;background&quot;, &quot;30c98a73d5f1fb7e6e3c1a52&quot;, &quot;30c98a73d5f1fb7e6e3c1a53&quot;, &quot;30c98a73d5f1fb7e6e3c1a54f&quot;], &quot;label_groups&quot;: [[&quot;background&quot;, &quot;30c98a73d5f1fb7e6e3c1a52&quot;, &quot;30c98a73d5f1fb7e6e3c1a53&quot;, &quot;30c98a73d5f1fb7e6e3c1a54&quot;]], &quot;ignore_index&quot;: 255}" />
            <labels value="background 30c98a73d5f1fb7e6e3c1a52 30c98a73d5f1fb7e6e3c1a53 30c98a73d5f1fb7e6e3c1a54" />
            <mean_values value="123.675 116.28 103.53" />
            <model_type value="Segmentation" />
            <optimization_config value="{&quot;advanced_parameters&quot;: {&quot;activations_range_estimator_params&quot;: {&quot;min&quot;: {&quot;statistics_type&quot;: &quot;QUANTILE&quot;, &quot;aggregator_type&quot;: &quot;MIN&quot;, &quot;quantile_outlier_prob&quot;: 0.0001}, &quot;max&quot;: {&quot;statistics_type&quot;: &quot;QUANTILE&quot;, &quot;aggregator_type&quot;: &quot;MAX&quot;, &quot;quantile_outlier_prob&quot;: 0.0001}}}}" />
            <pad_value value="0" />
            <resize_type value="standard" />
            <return_soft_prediction value="True" />
            <reverse_input_channels value="False" />
            <scale_values value="58.395 57.12 57.375" />
            <soft_threshold value="0.5" />
            <task_type value="segmentation" />
        </model_info>
    </rt_info>
</net>"""  # noqa: E501
        label_ids_xml_regex = r'<label_ids value=".*[0-9a-fA-F]{24}.*" />'
        label_ids_before_redaction = re.search(label_ids_xml_regex, model_xml_data)
        assert label_ids_before_redaction is not None, "Input data and/or regex are incorrectly built"
        labels_xml_regex = r'<labels value=".*[0-9a-fA-F]{24}.*" />'
        labels_before_redaction = re.search(labels_xml_regex, model_xml_data)
        assert labels_before_redaction is not None, "Input data and/or regex are incorrectly built"
        label_info_xml_regex = r'<label_info value=".*[0-9a-fA-F]{24}.*" />'
        label_info_before_redaction = re.search(label_info_xml_regex, model_xml_data)
        assert label_info_before_redaction is not None, "Input data and/or regex are incorrectly built"

        redacted_data = data_redaction_use_case.recreate_objectid_in_model_xml(model_xml_data=model_xml_data)

        redacted_data_str = redacted_data.decode("utf-8")
        assert "<?xml version" in redacted_data_str
        assert "<rt_info>" in redacted_data_str
        assert "<model_info>" in redacted_data_str
        label_ids_after_redaction = re.search(label_ids_xml_regex, redacted_data_str)
        assert label_ids_after_redaction is not None, "'label_ids' not found after redaction"
        assert label_ids_after_redaction.group() != label_ids_before_redaction.group(), "'label_ids' did not change"
        labels_after_redaction = re.search(labels_xml_regex, redacted_data_str)
        assert labels_after_redaction is not None, "'labels' not found after redaction"
        assert labels_after_redaction.group() != labels_before_redaction.group(), "'labels' did not change"
        label_info_after_redaction = re.search(label_info_xml_regex, redacted_data_str)
        assert label_info_after_redaction is not None, "'label_info' not found after redaction"
        assert label_info_after_redaction.group() != label_info_before_redaction.group(), "'label_info' did not change"

    def test_recreate_objectid_in_exportable_code_wheel(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase()
        # Create a .whl with similar structure of exportable code
        whl_files = [
            "model/model.xml",
            "model/model.bin",
            "model/config.json",
            "python/requirements.txt",
            "python/LICENSE",
            "python/demo.py",
            "README.md",
        ]
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            tempfile.NamedTemporaryFile(suffix=".whl", delete=False) as temp_zip,
            ZipFile(temp_zip.name, "w") as zipf,
        ):
            for arc_path in whl_files:
                fs_path = os.path.join(temp_dir, arc_path)
                os.makedirs(os.path.dirname(fs_path), exist_ok=True)
                with open(fs_path, "w") as fp:
                    fp.write("original_data")
                zipf.write(fs_path, arcname=arc_path)

        with (
            patch.object(
                data_redaction_use_case, "recreate_objectid_in_config_json", return_value="redacted_data"
            ) as mock_redact_json,
            patch.object(
                data_redaction_use_case, "recreate_objectid_in_model_xml", return_value="redacted_data"
            ) as mock_redact_xml,
        ):
            data_redaction_use_case.recreate_objectid_in_exportable_code_wheel(temp_zip.name)

        # Verify that the .xml and config.json where identified and redacted
        mock_redact_xml.assert_called_once_with("original_data")
        mock_redact_json.assert_called_once_with("original_data")
        # Verify that the output whl contains the same files as the original one
        with ZipFile(temp_zip.name, "r") as out_zipf:
            redacted_whl_files = [item.filename for item in out_zipf.infolist()]
        assert sorted(redacted_whl_files) == sorted(whl_files)

    @pytest.mark.parametrize(
        "file_path,is_model_xml,is_json_config,is_exportable_code",
        [
            ("weights_033d48b2-7fb0-4120-9816-1c21da956e4d.pth", False, False, False),
            ("openvino_91b5b988-e41d-47ff-962f-4b6cd0ff2d30.xml", True, False, False),
            ("label_schema_41f4b824-3b6c-4411-abd7-d9992044d213.json", False, True, False),
            ("reference_features_96f5a896-4fa7-4721-91ca-74dfae66f5df.json", False, True, False),
            ("exportable_code_56734cb5-a6aa-4179-963e-2df288e77d57.whl", False, False, True),
        ],
        ids=[
            "regular file",
            "model xml",
            "label schema json",
            "reference features json",
            "exportable code wheel",
        ],
    )
    def test_recreate_objectid_in_file(self, file_path, is_model_xml, is_json_config, is_exportable_code) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase()
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.object(
                data_redaction_use_case, "recreate_objectid_in_config_json", return_value="redacted_data"
            ) as mock_redact_json,
            patch.object(
                data_redaction_use_case, "recreate_objectid_in_model_xml", return_value=b"redacted_data"
            ) as mock_redact_xml,
            patch.object(
                data_redaction_use_case, "recreate_objectid_in_exportable_code_wheel", return_value="redacted_data"
            ) as mock_redact_whl,
        ):
            # Create the file
            file_path = os.path.join(temp_dir, file_path)
            with open(file_path, "w") as fp:
                fp.write("test_data")

            out_file_path = data_redaction_use_case.recreate_objectid_in_file(file_path)

        mock_redact_xml.assert_called() if is_model_xml else mock_redact_xml.assert_not_called()
        mock_redact_json.assert_called() if is_json_config else mock_redact_json.assert_not_called()
        mock_redact_whl.assert_called() if is_exportable_code else mock_redact_whl.assert_not_called()
        assert out_file_path == file_path

    def test_update_user_info_in_mongodb_doc(self, fxt_mongo_id) -> None:
        new_user_id = uuid.uuid4()
        data_redaction_use_case = ImportDataRedactionUseCase(user_replacement_new_id=new_user_id)
        bson_doc = (
            '{"_id": {"$sid": "30c98a73d5f1fb7e6e3c1a51"}, "user_id": "$user_id_str", '
            '"creator": "$user_id_uuid4", "author_name": "$user_id_uuid4", '
            '"some_id": {"$sid": "30c98a73d5f1fb7e6e3c1a52"}}'
        )
        json_options = JSONOptions(uuid_representation=UuidRepresentation.STANDARD)

        out_bson_doc = data_redaction_use_case.update_user_info_in_mongodb_doc(bson_doc=bson_doc)

        out_doc = loads(out_bson_doc, json_options=json_options)
        # Check that the expected fields are reconstructed
        assert out_doc["user_id"] == str(new_user_id)
        assert out_doc["creator"] == new_user_id
        assert out_doc["author_name"] == new_user_id
        # Check that the other fields still exist
        assert "_id" in out_doc
        assert "some_id" in out_doc

    def test_update_creation_time_in_mongodb_doc(self) -> None:
        data_redaction_use_case = ImportDataRedactionUseCase()

        doc_with_date = {"creation_date": "2021-01-01T00:00:00.000Z", "upload_date": "2021-01-01T00:00:00.000Z"}
        result_doc_with_data = data_redaction_use_case.update_creation_time_in_mongodb_doc(doc_with_date)
        assert result_doc_with_data["creation_date"] == data_redaction_use_case.import_date
        assert result_doc_with_data["upload_date"] == data_redaction_use_case.import_date

        doc_without_date = {"foo": "bar"}
        result_doc_without_data = data_redaction_use_case.update_creation_time_in_mongodb_doc(doc_without_date)
        assert result_doc_without_data == doc_without_date

    def test_sanitize_extension(self) -> None:
        # Arrange
        lowercase_file = "test_file.png"
        uppercase_file = "test_file.PNG"
        expected_file = lowercase_file

        # Act
        lowercase_result = ImportDataRedactionUseCase.sanitize_extension(lowercase_file)
        uppercase_result = ImportDataRedactionUseCase.sanitize_extension(uppercase_file)

        # Assert
        assert lowercase_result == expected_file
        assert uppercase_result == expected_file
