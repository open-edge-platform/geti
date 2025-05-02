import datumaro as dm
import pytest
from iai_core.entities.label import Domain

from jobs_common_extras.datumaro_conversion.definitions import SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES


@pytest.mark.CommonComponent
class TestDefinitions:
    @pytest.mark.parametrize(
        "domain,ann_types",
        [
            (Domain.CLASSIFICATION, {dm.AnnotationType.label}),
            (Domain.DETECTION, {dm.AnnotationType.bbox}),
            (
                Domain.SEGMENTATION,
                {
                    dm.AnnotationType.bbox,
                    dm.AnnotationType.polygon,
                    dm.AnnotationType.ellipse,
                    dm.AnnotationType.mask,
                },
            ),
            (
                Domain.INSTANCE_SEGMENTATION,
                {
                    dm.AnnotationType.bbox,
                    dm.AnnotationType.polygon,
                    dm.AnnotationType.ellipse,
                    dm.AnnotationType.mask,
                },
            ),
            (Domain.ROTATED_DETECTION, {dm.AnnotationType.polygon}),
            (
                Domain.ANOMALY_CLASSIFICATION,
                {dm.AnnotationType.label},
            ),
            (
                Domain.ANOMALY_DETECTION,
                {dm.AnnotationType.label, dm.AnnotationType.bbox},
            ),
            (
                Domain.ANOMALY_SEGMENTATION,
                {
                    dm.AnnotationType.label,
                    dm.AnnotationType.bbox,
                    dm.AnnotationType.polygon,
                    dm.AnnotationType.ellipse,
                    dm.AnnotationType.mask,
                },
            ),
        ],
    )
    def test_supported_domain_to_annotation_types(self, domain, ann_types):
        """
        This test exists for a reverse check to make sure that a developer
        should not forget to include any item in ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS mapping.
        If you add any item to ANNOTATION_TYPE_TO_SUPPORTED_DOMAINS, you also add the counter part to this test.
        """
        assert domain in SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES
        assert SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES[domain] == ann_types
