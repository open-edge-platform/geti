// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { DOMAIN } from '../../src/core/projects/core.interface';
import { paths } from '../../src/core/services/routes';
import { clickOutsidePopover } from '../utils/mouse';
import { test as baseTest } from './base-test';
import { AnnotationListPage } from './page-objects/annotator/annotation-list-page';
import { AnnotatorPage } from './page-objects/annotator/annotator-page';
import { BoundingBoxToolPage } from './page-objects/annotator/bounding-box-tool-page';
import { CircleToolPage } from './page-objects/annotator/circle-tool-page';
import { DetectionAssistantToolPage } from './page-objects/annotator/detection-assistant-tool-page';
import { ExplanationPage } from './page-objects/annotator/explanation-page';
import { InteractiveSegmentationToolPage } from './page-objects/annotator/interactive-segmentation-tool-page';
import { LabelShortcutsPage } from './page-objects/annotator/label-shortcuts-page';
import { ObjectColoringToolPage } from './page-objects/annotator/object-coloring-tool-page';
import { PolygonToolPage } from './page-objects/annotator/polygon-tool-page';
import { QuickSelectionToolPage } from './page-objects/annotator/quick-selection-tool-page';
import { RotatedBoundingBoxToolPage } from './page-objects/annotator/rotated-bounding-box-tool-page';
import { SegmentAnythingToolPage } from './page-objects/annotator/segment-anything-tool-page';
import { SelectionToolPage } from './page-objects/annotator/selection-tool-page';
import { StampToolPage } from './page-objects/annotator/stamp-tool-page';
import { TaskNavigationPage } from './page-objects/annotator/task-navigation-page';
import { UndoRedoPage } from './page-objects/annotator/undo-redo-page';

export const getAnnotatorImagePath = (imageId: string) =>
    paths.project.annotator.image({
        organizationId: '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633',
        workspaceId: '3ccc1615-5cd1-4d6c-a14b-95cd46d66ad9',
        projectId: '592f1b3b-89e9-4d27-8e77-d2dc68536cbd',
        datasetId: '879268ad-d499-4917-998a-d3272d75530e',
        imageId,
    });

interface AnnotatorFixtures {
    annotatorPath: string;
    annotatorPage: AnnotatorPage;
    annotationListPage: AnnotationListPage;
    labelShortcutsPage: LabelShortcutsPage;
    boundingBoxTool: BoundingBoxToolPage;
    rotatedBoundingBoxTool: RotatedBoundingBoxToolPage;
    circleTool: CircleToolPage;
    polygonTool: PolygonToolPage;
    quickSelectionTool: QuickSelectionToolPage;
    objectColoringTool: ObjectColoringToolPage;
    detectionAssistantTool: DetectionAssistantToolPage;
    interactiveSegmentationTool: InteractiveSegmentationToolPage;
    segmentAnythingTool: SegmentAnythingToolPage;
    stampTool: StampToolPage;
    selectionTool: SelectionToolPage;
    taskNavigation: TaskNavigationPage;
    undoRedo: UndoRedoPage;
    explanation: ExplanationPage;
}

export const annotatorTest = baseTest.extend<AnnotatorFixtures>({
    annotatorPath: ({}, use) => use(getAnnotatorImagePath('613a23866674c43ae7a777aa')),
    annotatorPage: async ({ page }, use) => {
        await use(new AnnotatorPage(page));
    },
    annotationListPage: async ({ page }, use) => {
        await use(new AnnotationListPage(page));
    },
    labelShortcutsPage: async ({ page }, use) => {
        await use(new LabelShortcutsPage(page));
    },
    boundingBoxTool: async ({ page }, use) => {
        await use(new BoundingBoxToolPage(page));
    },
    rotatedBoundingBoxTool: async ({ page }, use) => {
        await use(new RotatedBoundingBoxToolPage(page));
    },
    circleTool: async ({ page }, use) => {
        await use(new CircleToolPage(page));
    },
    polygonTool: async ({ page }, use) => {
        await use(new PolygonToolPage(page));
    },
    quickSelectionTool: async ({ page, boundingBoxTool }, use) => {
        await use(new QuickSelectionToolPage(page, boundingBoxTool));
    },
    objectColoringTool: async ({ page }, use) => {
        await use(new ObjectColoringToolPage(page));
    },
    detectionAssistantTool: async ({ page, boundingBoxTool, circleTool }, use) => {
        await use(new DetectionAssistantToolPage(page, boundingBoxTool, circleTool));
    },
    interactiveSegmentationTool: async ({ page, boundingBoxTool }, use) => {
        await use(new InteractiveSegmentationToolPage(page, boundingBoxTool));
    },
    segmentAnythingTool: async ({ page }, use) => {
        await use(new SegmentAnythingToolPage(page));
    },
    selectionTool: async ({ page }, use) => {
        await use(new SelectionToolPage(page));
    },
    stampTool: async ({ page, selectionTool }, use) => {
        await use(new StampToolPage(page, selectionTool));
    },
    taskNavigation: async ({ page }, use) => {
        await use(new TaskNavigationPage(page));
    },
    undoRedo: async ({ page }, use) => {
        await use(new UndoRedoPage(page));
    },
    explanation: async ({ page }, use) => {
        await use(new ExplanationPage(page));
    },
});

export const checkCommonElements = async (page: Page, domain: DOMAIN) => {
    await expect(page.getByRole('button', { name: 'Back' })).toBeVisible();

    if (![DOMAIN.CLASSIFICATION, DOMAIN.ANOMALY_CLASSIFICATION].includes(domain)) {
        await expect(page.getByLabel(/default label/i)).toBeVisible();
    }

    await expect(page.getByRole('button', { name: 'Selection', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'undo' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'redo' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Fit image to screen' })).toBeVisible();
    await expect(page.getByTestId('annotation-all-annotations-toggle-visibility')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Canvas adjustments' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Show dialog with hotkeys' })).toBeVisible();

    if (![DOMAIN.ANOMALY_DETECTION, DOMAIN.ANOMALY_CLASSIFICATION, DOMAIN.ANOMALY_SEGMENTATION].includes(domain)) {
        await expect(page.getByTestId('required-annotations-value')).toBeVisible();
    }

    if ([DOMAIN.ANOMALY_DETECTION, DOMAIN.ANOMALY_SEGMENTATION].includes(domain)) {
        await page.getByRole('button', { name: 'project performance' }).click();

        await expect(page.getByText('Project performance')).toBeVisible();

        await clickOutsidePopover(page);
    } else {
        await expect(page.getByLabel('Project score')).toBeVisible();
    }

    await expect(page.getByRole('button', { name: 'Jobs in progress' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Documentation actions' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();

    await expect(page.getByTestId('annotation-list-accordion')).toBeVisible();
    await expect(page.getByTestId('selected-annotation-dataset-id')).toBeVisible();
    await expect(page.getByTestId('annotations-canvas-image')).toBeVisible();
};

export const checkNumberOfTools = async (page: Page, number: number) => {
    const allTools = page
        .locator('[data-testid=base-drawing-tools-container] > button')
        .or(page.locator('[data-testid=smart-drawing-tools-container] > button'));

    await expect(allTools).toHaveCount(number);
};

export const checkSegmentationTools = async (page: Page) => {
    await expect(page.getByRole('button', { name: 'Bounding Box' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Detection assistant' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Circle' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Polygon' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Quick Selection' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Object coloring' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Interactive segmentation' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Auto segmentation' })).toBeVisible();
};

export const checkDetectionTools = async (page: Page) => {
    await expect(page.getByRole('button', { name: 'Bounding Box' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Detection assistant' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Auto segmentation' })).toBeVisible();
};

export const checkKeypointTools = async (page: Page) => {
    await expect(page.getByRole('button', { name: 'Selection' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Keypoint tool' })).toBeVisible();
};
