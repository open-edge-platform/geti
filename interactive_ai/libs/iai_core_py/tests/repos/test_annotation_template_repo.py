# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import pytest

from iai_core_py.entities.annotation_template import AnnotationTemplate, NullAnnotationTemplate
from iai_core_py.repos.annotation_template_repo import AnnotationTemplateRepo

from geti_types import ID, ProjectIdentifier


@pytest.fixture
def fxt_annotation_template_1():
    yield AnnotationTemplate(
        id_=ID("test_id_1"),
        name="test_name_1",
        value="test_value",
    )


@pytest.fixture
def fxt_annotation_template_2():
    yield AnnotationTemplate(
        id_=ID("test_id_2"),
        name="test_name_2",
        value="test_value",
    )


class TestAnnotationTemplateRepo:
    def test_annotation_template_repo(self, fxt_annotation_template_1, fxt_annotation_template_2) -> None:
        """
        <b>Description:</b>
        Check that an annotation template can be saved, retrieved, and deleted in the DB

        <b>Input data:</b>
        An annotation template

        <b>Expected results:</b>
        Test passes if the annotation template is saved, retrieved, and deleted in the DB

        <b>Steps</b>
        1. Save 2 annotation templates
        2. Retrieve the annotation templates one by one, and as all of them
        3. Delete the first annotation template
        4. Assert that the annotation template does not exist in the DB
        5. Delete all remain annotation templates
        6. Assert that the collection is empty
        """
        project_identifier = ProjectIdentifier(
            project_id=ID("test_id"),
            workspace_id=ID("test_workspace"),
        )
        repo = AnnotationTemplateRepo(project_identifier)

        repo.save(instance=fxt_annotation_template_1)
        repo.save(instance=fxt_annotation_template_2)

        annotation_template_1 = repo.get_by_id(id_=fxt_annotation_template_1.id_)
        annotation_template_2 = repo.get_by_id(id_=fxt_annotation_template_2.id_)
        annotation_templates = repo.get_all()
        assert annotation_template_1 == fxt_annotation_template_1
        assert annotation_template_2 == fxt_annotation_template_2
        assert set(annotation_templates) == {fxt_annotation_template_1, fxt_annotation_template_2}

        repo.delete_by_id(fxt_annotation_template_1.id_)
        null_annotation_template_1 = repo.get_by_id(id_=fxt_annotation_template_1.id_)
        assert null_annotation_template_1 == NullAnnotationTemplate()

        repo.delete_all()
        null_annotation_templates = repo.get_all()
        assert list(null_annotation_templates) == []
