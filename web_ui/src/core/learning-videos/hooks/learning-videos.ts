// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { LearningVideo } from '../dtos/learning-video.interface';

export const LEARNING_VIDEOS: LearningVideo[] = [
    {
        id: 'create-new-project-id',
        title: 'Creating a new project',
        description: 'In this tutorial, you will learn how to create a project in Geti.',
        video: '_static/videos/tutorials/ProjectCreation.mp4',
    },
    {
        id: 'create-hierarchical-classification-project',
        title: 'Creating a hierarchical classification project',
        description: 'In this tutorial, you will learn how to create a hierarchical classification project in Geti.',
        video: '_static/videos/tutorials/ProjectCreation-HierarchicalClassification.mp4',
    },
    {
        id: 'working-with-files-id',
        title: 'Working with files',
        description: 'In this tutorial, you will learn how to upload and manage files in Geti.',
        video: '_static/videos/tutorials/WorkingWithFiles.mp4',
    },
    {
        id: 'annotation-basics-object-detection-id',
        title: 'Annotation Basics for Object Detection',
        description: 'In this tutorial, you will learn how to annotate objects in Object Detection projects.',
        video: '_static/videos/tutorials/AnnotationBasics-Detection.mp4',
    },
    {
        id: 'annotation-basics-image-segmentation-id',
        title: 'Annotation Basics for Image Segmentation',
        description: 'In this tutorial, you will learn how to annotate objects in Image Segmentation projects.',
        video: '_static/videos/tutorials/AnnotationBasics-Segmentation.mp4',
    },
    {
        id: 'anomaly-segmentation-id',
        title: 'Anomaly Segmentation',
        description: 'In this tutorial, you will learn how to create a model that can detect and segment anomalies.',
        video: '_static/videos/tutorials/AnomalySegmentation.mp4',
    },
];
