// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
