// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MAX_SUPPORTED_ANNOTATIONS } from '../../../core/annotations/utils';
import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { DocsUrl } from '../tutorials/utils';

interface TutorialCardData {
    header: string | undefined;
    description: string;
    docUrl: DocsUrl | undefined;
}

export const getCardData = (cardKey: TUTORIAL_CARD_KEYS): TutorialCardData => {
    switch (cardKey) {
        case TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION:
            return {
                header: '',
                description:
                    `Define concise and descriptive labels for rectangular regions (bounding boxes)` +
                    ` that you will draw in images or frames. You may change the labels or extend ` +
                    `them after creating the project in the labels section when you enter your project.`,
                docUrl: DocsUrl.DETECTION,
            };
        case TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION_CHAIN:
            return {
                header: '',
                description:
                    `Define concise and descriptive label for rectangular regions (bounding boxes)` +
                    ` that you will draw in images or frames. Only one detection label is allowed. ` +
                    `You may change the label after creating the project in the labels section when ` +
                    `you enter your project.`,
                docUrl: DocsUrl.DETECTION,
            };
        case TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_SEGMENTATION:
            return {
                header: '',
                description:
                    `Define concise and descriptive labels for detailed outlines around objects` +
                    ` in images or frames. You may change the labels or extend them after creating` +
                    ` the project in the labels section when you enter your project.`,
                docUrl: DocsUrl.SEGMENTATION,
            };
        case TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_SINGLE_SELECTION:
            return {
                header: '',
                description:
                    `Create at least two descriptive labels to categorize entire images or frames, setting the ` +
                    `foundation for your training dataset. You may change the labels or extend them after ` +
                    `creating the project in the labels section when you enter your project.`,
                docUrl: DocsUrl.CLASSIFICATION,
            };
        case TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_MULTIPLE_SELECTION:
            return {
                header: '',
                description:
                    `Create at least two descriptive labels to categorize entire images or frames, setting the ` +
                    `foundation for your training dataset. You may change the labels or extend them after ` +
                    `creating the project in the labels section when you enter your project.`,
                docUrl: DocsUrl.CLASSIFICATION,
            };
        case TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_HIERARCHICAL:
            return {
                header: '',
                description:
                    'To create a label hierarchy, start with general categories and break them down into specific ' +
                    'subcategories, forming a tree-like structure that reflects their relationship. ' +
                    'You can create a hierarchical structure from Single or Multiselection with nested labels' +
                    ' from which you can choose one or multiple labels in a particular group. You may change that' +
                    ' labels or extend them after creating the project in the Labels view when you enter your project.',
                docUrl: DocsUrl.LABELS_CREATION,
            };
        case TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL:
            return {
                header: 'Building a good dataset',
                description:
                    `A robust dataset is the foundation of reliable AI models. Learn the essentials of dataset ` +
                    ` composition,\n annotation strategies, and quality checks to ensure your AI project is ` +
                    `built on solid ground.`,
                docUrl: DocsUrl.DATASET,
            };
        case TUTORIAL_CARD_KEYS.PROJECT_MODEL_TUTORIAL:
            return {
                header: 'No trained models detected',
                description:
                    `Before training your first model, you need to upload and annotate your dataset.` +
                    ` Once a model has been trained, come back to this screen to view the performance` +
                    ` details and further optimize your model.`,
                docUrl: DocsUrl.MODELS,
            };
        case TUTORIAL_CARD_KEYS.PROJECT_DEPLOYMENT_TUTORIAL:
            return {
                header: 'How to deploy your model',
                description: 'After thorough testing and optimization, your model is ready for real-world application.',
                docUrl: DocsUrl.DEPLOYMENT,
            };
        case TUTORIAL_CARD_KEYS.PROJECT_TESTS_TUTORIAL:
            return {
                header: 'How to test your model',
                description:
                    `Once your model is trained, it’s crucial to test its performance to ensure it meets your ` +
                    `standards for accuracy and reliability. Upload and annotate your test data, run tests to` +
                    ` evaluate your model on unseen data, and analyze the results to further refine the model.`,
                docUrl: DocsUrl.TESTS,
            };
        case TUTORIAL_CARD_KEYS.ANNOTATIONS_COUNT_LIMIT:
            return {
                header: '',
                description:
                    `This image contains more than the max amount of ${MAX_SUPPORTED_ANNOTATIONS}` +
                    ` allowed annotations. Please remove annotations or split the image into multiple images.`,
                docUrl: undefined,
            };
        default:
            return {
                header: '',
                description: '',
                docUrl: undefined,
            };
    }
};
