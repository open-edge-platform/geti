// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AnnotationDTO, AnnotationLabelDTO } from '../../src/core/annotations/dtos/annotation.interface';

// These two types lets us have mocked annotation and label data that include
// the name and color of labels.
export type LabelsWithNameAndColor = AnnotationLabelDTO & { name: string; color: string };
export type AnnotationDTOWithLabelProperties = AnnotationDTO & { labels: LabelsWithNameAndColor[] };
