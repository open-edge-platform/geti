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

import { expect, Locator } from '@playwright/test';

import { AnnotationDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import * as anomalyClassificationMock from './../../../mocks/anomaly/anomaly-classification/mocks';
import * as anomalyDetectionMock from './../../../mocks/anomaly/anomaly-detection/mocks';
import * as anomalySegmentationMock from './../../../mocks/anomaly/anomaly-segmentation/mocks';
import * as classification from './../../../mocks/classification/mocks';
import * as detectionClassification from './../../../mocks/detection-classification/mocks';
import * as detectionOrientedMock from './../../../mocks/detection-oriented/mocks';
import * as detectionSegmentation from './../../../mocks/detection-segmentation/mocks';
import * as detectionMock from './../../../mocks/detection/mocks';
import * as segmentationMock from './../../../mocks/segmentation/mocks';

const expectToolToBeActive = async (tool: Promise<Locator>) => {
    await expect(await tool).toHaveAttribute('aria-pressed', 'true');
};

const expectToolToBeVisible = async (tool: Promise<Locator>) => {
    await expect(await tool).toBeVisible();
};

const expectToolToBeInvisible = async (tool: Promise<Locator>) => {
    await expect(await tool).toBeHidden();
};

test.describe('ActiveTool', () => {
    test.describe('Available tools per tool and default tool', () => {
        test('Detection bounding box', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            rotatedBoundingBoxTool,
            polygonTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionMock.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionMock.media)));

            await page.goto(detectionMock.annotatorUrl);

            await expectToolToBeActive(boundingBoxTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
        });

        test('Detection oriented', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            rotatedBoundingBoxTool,
            polygonTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionOrientedMock.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionOrientedMock.media)));

            await page.goto(detectionOrientedMock.annotatorUrl);

            await expectToolToBeActive(rotatedBoundingBoxTool.getTool());

            await expectToolToBeVisible(boundingBoxTool.getTool());
            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());
            await expectToolToBeVisible(interactiveSegmentationTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
        });

        test('Segmentation', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(segmentationMock.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(segmentationMock.media)));

            await page.goto(segmentationMock.annotatorUrl);

            await expectToolToBeActive(polygonTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(boundingBoxTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());
            await expectToolToBeVisible(circleTool.getTool());
            await expectToolToBeVisible(objectColoringTool.getTool());
            await expectToolToBeVisible(quickSelectionTool.getTool());
            await expectToolToBeVisible(interactiveSegmentationTool.getTool());

            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });

        test('Classification', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(classification.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(classification.media)));

            await page.goto(classification.annotatorUrl);

            await expectToolToBeActive(selectionTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(boundingBoxTool.getTool());
            await expectToolToBeInvisible(detectionAssistantTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });

        test('Anomaly classification', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(anomalyClassificationMock.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(anomalyClassificationMock.media)));

            await page.goto(anomalyClassificationMock.annotatorUrl);

            await expectToolToBeActive(selectionTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(boundingBoxTool.getTool());
            await expectToolToBeInvisible(detectionAssistantTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });

        test('Anomaly detection', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            rotatedBoundingBoxTool,
            polygonTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(anomalyDetectionMock.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(anomalyDetectionMock.media)));

            await page.goto(anomalyDetectionMock.annotatorUrl);

            await expectToolToBeActive(boundingBoxTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
        });

        test('Anomaly segmentation', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(anomalySegmentationMock.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(anomalySegmentationMock.media)));

            await page.goto(anomalySegmentationMock.annotatorUrl);

            await expectToolToBeActive(polygonTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(boundingBoxTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());
            await expectToolToBeVisible(circleTool.getTool());
            await expectToolToBeVisible(objectColoringTool.getTool());
            await expectToolToBeVisible(quickSelectionTool.getTool());
            await expectToolToBeVisible(interactiveSegmentationTool.getTool());

            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });

        test('Detection -> Segmentation: All mode', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionSegmentation.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionSegmentation.media)));

            await page.goto(detectionSegmentation.annotatorUrl);

            await expectToolToBeActive(polygonTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(boundingBoxTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());
            await expectToolToBeVisible(circleTool.getTool());
            await expectToolToBeVisible(objectColoringTool.getTool());
            await expectToolToBeVisible(quickSelectionTool.getTool());
            await expectToolToBeVisible(interactiveSegmentationTool.getTool());

            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });

        test('Detection -> Segmentation: Detection mode', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
            taskNavigation,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionSegmentation.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionSegmentation.media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));

            await page.goto(detectionSegmentation.annotatorUrl);
            await taskNavigation.selectTaskMode('Detection');

            await expectToolToBeActive(boundingBoxTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
        });

        test('Detection -> Segmentation: Segmentation mode', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionSegmentation.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionSegmentation.media)));

            await page.goto(detectionSegmentation.annotatorUrl);

            await expectToolToBeActive(polygonTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(boundingBoxTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());
            await expectToolToBeVisible(circleTool.getTool());
            await expectToolToBeVisible(objectColoringTool.getTool());
            await expectToolToBeVisible(quickSelectionTool.getTool());
            await expectToolToBeVisible(interactiveSegmentationTool.getTool());

            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });

        test('Detection -> Classification: All mode', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionClassification.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionClassification.media)));

            await page.goto(detectionClassification.annotatorUrl);

            await expectToolToBeActive(boundingBoxTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
        });

        test('Detection -> Classification: Detection mode', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
            taskNavigation,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionClassification.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionClassification.media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));

            await page.goto(detectionClassification.annotatorUrl);
            await taskNavigation.selectTaskMode('Detection');

            await expectToolToBeActive(boundingBoxTool.getTool());

            await expectToolToBeVisible(selectionTool.getTool());
            await expectToolToBeVisible(detectionAssistantTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
        });

        test('Detection -> Classification: Classification mode', async ({
            registerApiResponse,
            page,
            boundingBoxTool,
            selectionTool,
            circleTool,
            detectionAssistantTool,
            objectColoringTool,
            quickSelectionTool,
            interactiveSegmentationTool,
            polygonTool,
            rotatedBoundingBoxTool,
            taskNavigation,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionClassification.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionClassification.media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));

            await page.goto(detectionClassification.annotatorUrl);
            await taskNavigation.selectTaskMode('Classification');

            await expectToolToBeActive(selectionTool.getTool());

            await expectToolToBeInvisible(polygonTool.getTool());
            await expectToolToBeInvisible(boundingBoxTool.getTool());
            await expectToolToBeInvisible(detectionAssistantTool.getTool());
            await expectToolToBeInvisible(circleTool.getTool());
            await expectToolToBeInvisible(objectColoringTool.getTool());
            await expectToolToBeInvisible(quickSelectionTool.getTool());
            await expectToolToBeInvisible(interactiveSegmentationTool.getTool());
            await expectToolToBeInvisible(rotatedBoundingBoxTool.getTool());
        });
    });

    test.describe("Selected tool should use last used tool's settings", () => {
        test.describe('Single task', () => {
            const [segmentationAnnotation] = segmentationMock.userAnnotationsResponse.annotations as AnnotationDTO[];

            test.beforeEach(async ({ registerApiResponse, page }) => {
                registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(segmentationMock.project)));
                registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(segmentationMock.media)));
                registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                    res(ctx.json(segmentationMock.userAnnotationsResponse))
                );

                await page.goto(detectionSegmentation.annotatorUrl);
            });

            test('Detection assistant tool', async ({ detectionAssistantTool, boundingBoxTool }) => {
                await detectionAssistantTool.selectTool();

                await detectionAssistantTool.selectCircleMode();
                await detectionAssistantTool.toggleAutoMergeDuplicates();

                await boundingBoxTool.selectTool();

                await detectionAssistantTool.selectTool();

                await expect(await detectionAssistantTool.getCircleMode()).toBeVisible();
                await expect(await detectionAssistantTool.getAutoMergeDuplicatesToggle()).not.toBeChecked();
            });

            test('Circle tool', async ({ circleTool, boundingBoxTool }) => {
                await circleTool.selectTool();

                await circleTool.changeRadius(10);

                const radiusValue = await circleTool.getRadiusSliderValue();

                await boundingBoxTool.selectTool();

                await circleTool.selectTool();

                expect(await circleTool.getRadiusSliderValue()).toBe(radiusValue);
            });

            test('Polygon tool', async ({ polygonTool, boundingBoxTool }) => {
                await polygonTool.selectTool();

                await polygonTool.toggleSnappingMode();

                await expect(await polygonTool.getSnappingMode()).toBeChecked();

                await boundingBoxTool.selectTool();

                await polygonTool.selectTool();

                await expect(await polygonTool.getSnappingMode()).toBeChecked();
            });

            test('Quick selection', async ({ page, quickSelectionTool, boundingBoxTool }) => {
                await quickSelectionTool.selectTool();

                await quickSelectionTool.changeSensitivity(100);

                const sensitivityValue = await quickSelectionTool.getSensitivitySliderValue();

                // eslint-disable-next-line playwright/no-force-option
                await page.getByText('Quick selection').click({ force: true });

                await boundingBoxTool.selectTool();

                await quickSelectionTool.selectTool();

                await quickSelectionTool.openSensitivityButton();

                expect(await quickSelectionTool.getSensitivitySliderValue()).toBe(sensitivityValue);
            });

            test('Object coloring', async ({ page, objectColoringTool, boundingBoxTool }) => {
                const BRUSH_SLIDER_POINTS = [525, 535];
                await objectColoringTool.selectTool();

                await objectColoringTool.changeBrushSize(BRUSH_SLIDER_POINTS[0], BRUSH_SLIDER_POINTS[1]);

                await objectColoringTool.openBrushSlider();

                const brushValue = await objectColoringTool.getBrushSliderValue();

                // eslint-disable-next-line playwright/no-force-option
                await page.getByText('Object coloring').click({ force: true });

                await boundingBoxTool.selectTool();

                await objectColoringTool.selectTool();

                await objectColoringTool.openBrushSlider();
                expect(await objectColoringTool.getBrushSliderValue()).toBe(brushValue);
            });

            test('Interactive segmentation', async ({ interactiveSegmentationTool, boundingBoxTool }) => {
                await interactiveSegmentationTool.selectTool();

                await interactiveSegmentationTool.toggleDynamicSelectionMode();
                await interactiveSegmentationTool.toggleRightClickMode();

                await boundingBoxTool.selectTool();

                await interactiveSegmentationTool.selectTool();

                await expect(await interactiveSegmentationTool.getDynamicSelectionMode()).not.toBeChecked();
                await expect(await interactiveSegmentationTool.getRightClickMode()).toBeChecked();
            });

            test('Selection tool should always reset to the default sub tool', async ({
                page,
                selectionTool,
                stampTool,
                boundingBoxTool,
            }) => {
                await selectionTool.selectTool();

                await selectionTool.selectUsingClick(segmentationAnnotation.shape);

                await stampTool.selectStampToolUsingButton();

                await expect(page.getByRole('button', { name: 'Cancel stamp' })).toBeVisible();

                await boundingBoxTool.selectTool();

                await selectionTool.selectTool();

                await expect(page.getByRole('button', { name: 'Cancel stamp' })).toBeHidden();
            });
        });

        test.describe('Task chain', () => {
            test.beforeEach(async ({ registerApiResponse, page }) => {
                registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionSegmentation.project)));
                registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionSegmentation.media)));
                registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                    res(ctx.json(detectionSegmentation.userAnnotationsDetectionSegmentationResponse))
                );

                await page.goto(detectionSegmentation.annotatorUrl);
            });

            test('Selected tool is persistent in the task context', async ({
                boundingBoxTool,
                polygonTool,
                interactiveSegmentationTool,
                detectionAssistantTool,
                circleTool,
                taskNavigation,
            }) => {
                await expectToolToBeActive(polygonTool.getTool());
                await circleTool.selectTool();
                await expectToolToBeActive(circleTool.getTool());

                await taskNavigation.selectTaskMode('Detection');

                await expectToolToBeActive(boundingBoxTool.getTool());
                await detectionAssistantTool.selectTool();
                await expectToolToBeActive(detectionAssistantTool.getTool());

                await taskNavigation.selectTaskMode('Segmentation');

                await expectToolToBeActive(polygonTool.getTool());
                await interactiveSegmentationTool.selectTool();
                await expectToolToBeActive(interactiveSegmentationTool.getTool());

                await taskNavigation.selectTaskMode('Detection');
                await expectToolToBeActive(detectionAssistantTool.getTool());

                await taskNavigation.selectTaskMode('Segmentation');
                await expectToolToBeActive(interactiveSegmentationTool.getTool());

                await taskNavigation.selectTaskMode('All Tasks');
                await expectToolToBeActive(circleTool.getTool());
            });

            test('Selected tool is persistent in the task context - selection sub tool', async ({
                page,
                stampTool,
                selectionTool,
                taskNavigation,
            }) => {
                const [segmentationAnnotation] = detectionSegmentation.userAnnotationsDetectionSegmentationResponse
                    .annotations as AnnotationDTO[];

                await selectionTool.selectTool();

                await selectionTool.selectUsingClick(segmentationAnnotation.shape);
                await stampTool.selectStampToolUsingButton();

                await expect(page.getByRole('button', { name: 'Cancel stamp' })).toBeVisible();

                await taskNavigation.selectTaskMode('Detection');
                await taskNavigation.selectTaskMode('All Tasks');

                await expect(page.getByRole('button', { name: 'Cancel stamp' })).toBeVisible();
            });

            test("Selected tool's config is persistent in the task context", async ({
                polygonTool,
                circleTool,
                taskNavigation,
            }) => {
                await expectToolToBeActive(polygonTool.getTool());
                await circleTool.selectTool();
                await circleTool.changeRadius(50);
                const radiusValueInAllMode = await circleTool.getRadiusSliderValue();

                await taskNavigation.selectTaskMode('Segmentation');

                await circleTool.selectTool();

                const radiusValueInSegmentationMode = await circleTool.getRadiusSliderValue();

                expect(radiusValueInAllMode).not.toBe(radiusValueInSegmentationMode);

                await taskNavigation.selectTaskMode('All Tasks');
                expect(await circleTool.getRadiusSliderValue()).toBe(radiusValueInAllMode);

                await taskNavigation.selectTaskMode('Segmentation');
                expect(await circleTool.getRadiusSliderValue()).toBe(radiusValueInSegmentationMode);
            });
        });
    });
});
