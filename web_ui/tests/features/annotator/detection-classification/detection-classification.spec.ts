// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import * as path from 'path';

import { expect, Page } from '@playwright/test';

import { SHAPE_TYPE_DTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { DOMAIN } from '../../../../src/core/projects/core.interface';
import { OpenApiRequestBody, OpenApiResponseBody } from '../../../../src/core/server/types';
import { delay } from '../../../../src/shared/utils';
import { checkCommonElements, checkNumberOfTools, annotatorTest as test } from '../../../fixtures/annotator-test';
import {
    annotatorUrl,
    cardAnnotations,
    cardLabelId,
    detectionLabels,
    media,
    modelGroups,
    project,
    userDetectionAnnotationsClassificationResponse,
    userDetectionAnnotationsResponse,
} from '../../../mocks/detection-classification/mocks';
import {
    AnnotationDTOWithLabelProperties as AnnotationDTO,
    LabelsWithNameAndColor as AnnotationLabelDTO,
} from '../../../utils/annotation';
import { registerFullImage, registerStoreSettings } from '../../../utils/api';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import { resolveTestAssetPath } from '../../../utils/dataset';
import { getDirname } from '../../../utils/get-dirname';
import {
    expectAGlobalAnnotationToExist,
    expectAnnotationToHaveLabels,
    getGlobalAnnotation,
} from '../../project-tests/expect';
import { annotationResponse as cardsAnnotationsResponse } from '../filter-annotations/mocks';
import { toggleShowPredictions } from '../utils';

const getTaskTab = (page: Page, taskName: string) =>
    page.getByRole('navigation', { name: 'navigation-breadcrumbs' }).getByText(taskName);

const goToClassification = (page: Page) => getTaskTab(page, 'Classification').click();

const goToDetection = (page: Page) => getTaskTab(page, 'Detection').click();

const toPrediction = (annotation: AnnotationDTO): AnnotationDTO => {
    const labels = annotation.labels.map((label: AnnotationLabelDTO) => ({
        ...label,
        source: {
            user_id: null,
            model_id: '61387685df33ae8280c347b2',
            model_storage_id: '62387685df33ae8280c63a34',
        },
        probability: 0.33,
    }));

    return { ...annotation, labels };
};

const withoutDetectionlabels = (labels: AnnotationLabelDTO[]) => {
    return labels.filter((label) => !detectionLabels.some(({ id }) => id === label.id));
};

const filterByRoiQuery = (annotations: AnnotationDTO[], roiQuery: string) => {
    const [x, y, width, height] = roiQuery.split(',');

    // Find the prediction corresponding to the given ROI
    return annotations.filter(({ shape }) => {
        if (shape.type === SHAPE_TYPE_DTO.RECTANGLE) {
            return (
                shape.x === Number(x) &&
                shape.y === Number(y) &&
                shape.width === Number(width) &&
                shape.height === Number(height)
            );
        }
        return false;
    });
};

const annotations = [
    cardAnnotations[0],
    cardAnnotations[1],
    cardAnnotations[2],
    cardAnnotations[3],
    cardAnnotations[4],
];
const predictions = cardAnnotations.map(toPrediction);

test.describe(`Detection -> Classification`, () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));

        registerFullImage(registerApiResponse, resolveTestAssetPath('multiple-cards.webp'));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userDetectionAnnotationsResponse, annotations }))
        );
        registerApiResponse('GetSinglePrediction', (req, res, ctx) => {
            const roi = req.query.roi;

            if (roi !== undefined) {
                return res(ctx.json({ predictions: filterByRoiQuery(predictions, roi) }));
            }

            return res(ctx.json({ predictions }));
        });

        registerApiResponse('GetSingleExplanation', async (req, res, ctx) => {
            const roi = req.query.roi;
            const globalPredictions = roi === undefined ? predictions : filterByRoiQuery(predictions, roi);

            return res(
                ctx.json({
                    maps: globalPredictions.flatMap((prediction) =>
                        prediction.labels.map((label: AnnotationLabelDTO) => {
                            return {
                                // eslint-disable-next-line max-len
                                data: '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBgUGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/wAALCAAGAAgBAREA/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APyq+Ov7Tf7GuqfDH4u/Cz4G6X8XYrXxBN4Ot/h2fFHiScxR2ekxTxXX9p28eoPBK5DxfZ18uZIPnEQt1OD/AP/Z',
                                label_id: label.id,
                                label_name: label.name,
                            };
                        })
                    ),
                    created: '2023-11-07 14:57:03.371633532 +0000',
                    media_identifier: {
                        image_id: '6548cac2e645c2fbcd20b7b2',
                        type: 'image',
                    },
                })
            );
        });
    });

    test('Annotations and predictions', async ({ page }) => {
        await page.goto(annotatorUrl);

        await goToDetection(page);

        // Check that the default label combobox is set
        await expect(page.getByLabel('Selected default label')).toContainText(detectionLabels[0].name);

        await goToClassification(page);

        await expectAGlobalAnnotationToExist(page);

        const idx = annotations.length - 1;
        await expectAnnotationToHaveLabels(
            await getGlobalAnnotation(page),
            withoutDetectionlabels(annotations[idx].labels)
        );

        await page.getByRole('button', { name: 'Select annotation mode' }).click();
        await page.getByRole('button', { name: 'Select prediction mode' }).click();

        await expectAnnotationToHaveLabels(
            await getGlobalAnnotation(page),
            withoutDetectionlabels(predictions[idx].labels)
        );

        await expect(page.getByRole('button', { name: 'Use predictions' })).toBeEnabled();
        await page.getByRole('button', { name: 'Use predictions' }).click();
        await page.getByRole('button', { name: 'Replace' }).click();

        await expectAnnotationToHaveLabels(
            await getGlobalAnnotation(page),
            withoutDetectionlabels(predictions[idx].labels)
        );
    });

    test('No annotations, no predictions', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userDetectionAnnotationsResponse, annotations: [] }))
        );
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));

        await page.goto(annotatorUrl);

        await annotationListPage.expectTotalAnnotationsToBe(0);
    });

    test('No annotations, predicted annotation', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userDetectionAnnotationsResponse, annotations: [] }))
        );

        await page.goto(annotatorUrl);

        await annotationListPage.expectTotalAnnotationsToBe(predictions.length);
    });

    test('Annotations, no predicted annotation', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));

        await page.goto(annotatorUrl);

        await annotationListPage.expectTotalAnnotationsToBe(annotations.length);
    });

    test('Annotator page elements', async ({ page, registerApiExample }) => {
        registerApiExample('GetProjectStatus', 'Waiting for classification annotations');
        await page.goto(annotatorUrl);

        await waitForLoadingToBeFinished(page);

        await expect(page.locator('[id=breadcrumb-all-tasks]')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('[id="breadcrumb-Detection"]')).toBeVisible();
        await expect(page.locator('[id="breadcrumb-Classification"]')).toBeVisible();

        await checkNumberOfTools(page, 3);

        await checkCommonElements(page, DOMAIN.CLASSIFICATION);
    });

    test('Predictions for second task should be available', async ({ page, registerApiResponse, openApi }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => {
            const { mock } = openApi.mockResponseForOperation('GetImageDetail') as {
                status: number;
                mock: OpenApiResponseBody<'GetImageDetail'>;
            };

            return res(
                ctx.json({
                    ...mock,
                    id: '613a23866674c43ae7a777aa',
                    // We need to overwrite the annotation state so that it is not revisit, which
                    // would make submit always save regardless of unsaved changes
                    annotation_state_per_task: [{ task_id: '61012cdb1d38a5e71ef3bafd', state: 'none' }],
                })
            );
        });

        registerFullImage(
            registerApiResponse,
            path.resolve(getDirname(import.meta.url), './../filter-annotations/many-cards.jpeg')
        );

        // Setup for annotation & prediction behaviour
        let storedAnnotations: OpenApiRequestBody<'CreateImageAnnotation'>['annotations'] = [];

        // Annotations & Predictions setup
        // User Annotations: 12 cards where 8 of them have been given classificaion labels
        // Predictions: 12 cards where each of them have been given classification labels
        //
        const annotationsWithoutClassificationLabel = [0, 1, 3, 5];
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
            const annotationsOld = cardsAnnotationsResponse.annotations.map((annotation, index) => {
                const labels = annotationsWithoutClassificationLabel.includes(index)
                    ? annotation.labels.filter(({ name }) => name === 'Card')
                    : annotation.labels;

                return { ...annotation, labels };
            });

            return res(ctx.json({ ...cardsAnnotationsResponse, annotations: annotationsOld }));
        });

        registerApiResponse('GetSinglePrediction', (req, res, ctx) => {
            const roi = req.query.roi;

            if (roi !== undefined) {
                const source = { model_id: 'model-id', model_storage_id: 'model-storage-id', user_id: null };
                const [x, y, width, height] = roi.split(',');

                // Find the prediction correspondong to the given ROI
                const predictionsForROI = cardsAnnotationsResponse.annotations
                    .filter(({ shape }) => {
                        if (shape.type === SHAPE_TYPE_DTO.RECTANGLE) {
                            return (
                                shape.x === Number(x) &&
                                shape.y === Number(y) &&
                                shape.width === Number(width) &&
                                shape.height === Number(height)
                            );
                        }
                        return false;
                    })
                    .map((annotation) => {
                        const labels = annotation.labels.map((label) =>
                            label.name === 'Card' ? label : { ...label, probability: Math.random(), source }
                        );
                        return { ...annotation, labels };
                    });

                return res(ctx.json({ predictions: predictionsForROI }));
            }

            return res(ctx.json({ predictions: annotations }));
        });

        registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
            storedAnnotations = req.body.annotations.map((annotation) => {
                return {
                    ...annotation,
                    labels: annotation.labels.map((label) => {
                        return {
                            ...label,
                            source: {
                                user_id: 'user',
                                model_id: null,
                                model_storage_id: null,
                            },
                        };
                    }),
                };
            });

            return res(ctx.status(200), ctx.json({ annotations: storedAnnotations, annotation_state_per_task: [] }));
        });

        await page.goto(`${annotatorUrl}?task-id=6101254defba22ca453f11d1`);

        //new implementation requires to media opening to load predictions
        await page.getByLabel('Annotation 97845455-6099-482f-ba1d-189955a1c57e').click();
        await page.getByLabel('Annotation 2beec505-085e-4ebb-8b2e-c20cf00353b7').click();
        await page.getByLabel('Annotation 16bf946c-50ec-42c6-9257-f5c6478eda34').click();
        await page.getByLabel('Annotation 42a249a2-8173-4a61-be5c-c9a74062121f').click();

        await page.getByRole('button', { name: /submit annotations/i }).click();

        // Expect that we submitted both the user's existing classification and the
        // predicted classification labels
        expect(storedAnnotations).toHaveLength(cardsAnnotationsResponse.annotations.length);

        storedAnnotations.forEach((annotation, index) => {
            expect(annotation.labels).toHaveLength(3);

            // Check that the annotations that did not have a classification label are now given,
            // the labels from prediction
            if (annotationsWithoutClassificationLabel.includes(index)) {
                annotation.labels
                    .filter((label) => label.id !== cardLabelId)
                    .forEach((label) => {
                        // @ts-expect-error we send more data than the OpenAPI schema expects
                        expect(label.probability).not.toEqual(1);
                    });
            }
        });

        // Check that we've selected the next media item
        await expect(() => {
            return expect(page.url()).not.toEqual(`${annotatorUrl}?task-id=63d8cec1ac620f32e365aca3`);
        }).toPass();
    });

    test('It loads predictions when loading model groups is slow', async ({
        page,
        annotationListPage,
        boundingBoxTool,
        registerApiResponse,
    }) => {
        registerApiResponse('GetModelGroups', async (_, res, ctx) => {
            // Mimick a slowly loading server
            await delay(10_000);

            return res(ctx.json({ model_groups: modelGroups }));
        });

        registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
            return res(ctx.json({ ...cardsAnnotationsResponse, annotations: [] }));
        });

        await page.goto(annotatorUrl);

        await boundingBoxTool.selectTool();
        await annotationListPage.expectTotalAnnotationsToBe(10);
    });

    test.describe('Explanation', () => {
        test('empty explanation', async ({ page, registerApiResponse, explanation }) => {
            registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));
            registerApiResponse('GetSingleExplanation', (_, res, ctx) => res(ctx.json({ maps: [] })));

            await page.goto(annotatorUrl);
            await goToDetection(page);
            await page.locator('role=button[name="Select prediction mode"]').click();

            const explanationButton = await explanation.getExplanationButton();

            await expect(explanationButton).toBeDisabled();
        });

        test('disable for "all tasks"', async ({ page, explanation }) => {
            await page.goto(annotatorUrl);
            await page.locator('role=button[name="Select prediction mode"]').click();
            await page.locator('role=navigation[name="navigation-breadcrumbs"]').locator('text="All Tasks"').click();

            const explanationButton = await explanation.getExplanationButton();

            await expect(explanationButton).toBeDisabled();
        });
    });

    test.describe('Annotation mode', () => {
        test.beforeEach(async ({ registerApiResponse }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userDetectionAnnotationsClassificationResponse, annotations: [] }))
            );
        });

        test('disable initial prediction as annotations', async ({ registerApiResponse, annotationListPage, page }) => {
            registerStoreSettings(registerApiResponse);
            await page.goto(annotatorUrl);

            await toggleShowPredictions(page, false);

            await annotationListPage.expectTotalAnnotationsToBe(predictions.length);

            await page.reload();
            await page.goto(annotatorUrl);

            await annotationListPage.expectTotalAnnotationsToBe(0);
        });

        test('enable initial prediction as annotations', async ({ registerApiResponse, annotationListPage, page }) => {
            registerStoreSettings(registerApiResponse);
            await page.goto(annotatorUrl);

            await toggleShowPredictions(page, true);

            await page.reload();
            await page.goto(annotatorUrl);

            await annotationListPage.expectTotalAnnotationsToBe(predictions.length);
        });
    });

    test.describe('Prediction mode', () => {
        test('Detection: overlap annotations', async ({ page, annotationListPage }) => {
            await page.goto(annotatorUrl);

            await page.locator('role=navigation[name="navigation-breadcrumbs"]').locator('text="Detection"').click();

            await annotationListPage.expectTotalAnnotationsToBe(annotations.length);

            await page.locator('role=button[name="Select prediction mode"]').click();

            const annotationContainer = page.getByLabel('annotations', { exact: true });

            const annotationsShapes = annotationContainer.locator('rect');
            await expect(annotationsShapes).toHaveCount(predictions.length);

            await page.locator('role=switch[name="overlap annotations"]').click();

            await expect(annotationsShapes).toHaveCount(annotations.length + predictions.length);
        });

        // eslint-disable-next-line max-len
        test('It does not reset annotations when switching to online predictions and back to active learning mode', async ({
            page,
            annotationListPage,
            boundingBoxTool,
            registerApiResponse,
        }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(ctx.json({ ...cardsAnnotationsResponse, annotations: [] }));
            });

            await page.goto(annotatorUrl);

            await annotationListPage.expectTotalAnnotationsToBe(10);

            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox({ x: 10, y: 10, width: 100, height: 100 });

            await annotationListPage.expectTotalAnnotationsToBe(11);

            await page.locator('role=button[name="Select prediction mode"]').click();

            await page.locator('role=button[name="Select annotation mode"]').click();
            await annotationListPage.expectTotalAnnotationsToBe(11);
        });
    });

    test.describe('Classification', () => {
        test('In AI prediction mode predictions become hidden when showing annotations', async ({ page }) => {
            await page.goto(annotatorUrl);

            await page
                .locator('role=navigation[name="navigation-breadcrumbs"]')
                .locator('text="Classification"')
                .click();

            await page.locator('role=button[name="Select prediction mode"]').click();

            const idx = annotations.length - 1;
            const globalAnnotation = await getGlobalAnnotation(page);
            await expectAnnotationToHaveLabels(globalAnnotation, withoutDetectionlabels(predictions[idx].labels));

            await page.locator('role=switch[name="overlap annotations"]').click();

            await expectAnnotationToHaveLabels(globalAnnotation, withoutDetectionlabels(annotations[idx].labels));
        });

        test('clicking prediction list element get selected', async ({ page }) => {
            await page.goto(annotatorUrl);

            await goToClassification(page);
            await page.locator('role=button[name="Select prediction mode"]').click();

            const predictionAnnotationId = annotations[0].id;
            const predictionAnnotationIdTwo = annotations[3].id;
            const thumbnail = page.getByTestId(`annotation-${predictionAnnotationId}-thumbnailWrapper`);
            await thumbnail.click();
            await expect(thumbnail).toHaveClass(/isSelected/);

            const thumbnailTwo = page.getByTestId(`annotation-${predictionAnnotationIdTwo}-thumbnailWrapper`);
            await thumbnailTwo.click();
            await expect(thumbnailTwo).toHaveClass(/isSelected/);
        });
    });

    test('render submit/use predictions', async ({ page }) => {
        await page.goto(annotatorUrl);

        await expect(page.getByRole('button', { name: 'Submit annotations' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Submit annotations' })).toHaveText('Submit »');

        await page.locator('role=button[name="Select prediction mode"]').click();

        await expect(page.locator('role=button[name="Use predictions"]')).toBeVisible();
        await expect(page.locator('role=button[name="Submit annotations"]')).toBeHidden();
    });

    test('redirect to `active mode` after replace/merge prediction', async ({ page }) => {
        await page.goto(annotatorUrl);

        await page.locator('role=button[name="Select prediction mode"]').click();

        const usePredictions = page.locator('role=button[name="Use predictions"]');
        await expect(usePredictions).toBeVisible();
        await usePredictions.click();

        expect(page.url()).toContain('mode=predictions');
        const replaceAnnotations = page.locator('role=button[name="Replace"]');
        await expect(replaceAnnotations).toBeVisible();
        await replaceAnnotations.click();
        expect(page.url()).toContain('mode=active-learning');
    });
});
