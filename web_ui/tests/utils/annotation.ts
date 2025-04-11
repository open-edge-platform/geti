// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AnnotationDTO, AnnotationLabelDTO } from '../../src/core/annotations/dtos/annotation.interface';

// These two types lets us have mocked annotation and label data that include
// the name and color of labels.
export type LabelsWithNameAndColor = AnnotationLabelDTO & { name: string; color: string };
export type AnnotationDTOWithLabelProperties = AnnotationDTO & { labels: LabelsWithNameAndColor[] };
