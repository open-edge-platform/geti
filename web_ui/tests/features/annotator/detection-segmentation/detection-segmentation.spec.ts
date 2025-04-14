// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { AnnotationDTO, SHAPE_TYPE_DTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { DOMAIN } from '../../../../src/core/projects/core.interface';
import { delay, getIds } from '../../../../src/shared/utils';
import { checkCommonElements, checkNumberOfTools, annotatorTest as test } from '../../../fixtures/annotator-test';
import { OpenApiFixtures } from '../../../fixtures/open-api';
import { settings } from '../../../fixtures/open-api/mocks';
import { registerStoreSettings } from '../../../utils/api';
import { expectAnnotationVisible } from '../expect';
import { toggleShowPredictions } from '../utils';
import {
    animalLabelId,
    annotatorUrl,
    deerLabelId,
    detectionLabels,
    media,
    predictionAnnotationId,
    predictionAnnotationsResponse,
    project,
    segmentationLabels,
    userAnnotationId,
    userAnnotationsResponse,
} from './../../../mocks/detection-segmentation/mocks';
import {
    expect,
    expectAnnotationIsVisible,
    expectNotToHaveAnnotationInputWithAnnotatedStatus,
    expectSubmitToBeEnabled,
    expectToHaveAnnotationInputWithAnnotatedStatus,
} from './expect';
import { annotations, predictions } from './mocks';

const getTaskNavigationTab = (page: Page, taskName: string) =>
    page.getByRole('navigation', { name: 'navigation-breadcrumbs' }).getByText(taskName);

const goToSegmentation = async (page: Page) => getTaskNavigationTab(page, 'Segmentation').click();

const goToDetection = (page: Page) => getTaskNavigationTab(page, 'Detection').click();

const goToAllTask = (page: Page) => getTaskNavigationTab(page, 'All Tasks').click();

const detectionId = project.pipeline.tasks[1].id;
const segmentationId = project.pipeline.tasks[3].id;

const isAnimalLabel = ({ id }: { id: string }) => id === animalLabelId;
const filterInputs = ({ labels }: { labels: { id: string }[] }) => labels.some(isAnimalLabel);

const replaceAnnotationsByPredictions = async (page: Page) => {
    await page.getByRole('button', { name: 'Select prediction mode' }).click();

    await expect(page.getByRole('button', { name: 'Use predictions' })).toBeEnabled();

    await page.getByRole('button', { name: 'Use predictions' }).click();
    await page.getByRole('button', { name: 'Replace' }).click();
};

const setToUserId = (labels: { id: string; name: string; source: { [k: string]: string | null } }[]) =>
    labels.map((label) => ({
        ...label,
        probability: 1.0,
        source: { ...label.source, user_id: 'default_user' },
    }));

const registerStoreAnnotations = (registerApiResponse: OpenApiFixtures['registerApiResponse']) => {
    const storedAnnotations: AnnotationDTO[][] = [];
    registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
        storedAnnotations.push(req.body.annotations as AnnotationDTO[]);

        return res(
            ctx.json({
                annotation_state_per_task: [],
                annotations: req.body.annotations.map((annotation) => ({
                    ...annotation,
                    labels: annotation.labels.map((label) => ({
                        ...label,
                        source: { user_id: 'user@test.com' },
                    })),
                })),
            })
        );
    });

    return storedAnnotations;
};

const getSubmitButton = (page: Page) => page.getByRole('button', { name: /submit annotations/i });

test.beforeEach(async ({ registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
    registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));

    registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
        res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
    );
});

test.describe(`Detection -> Segmentation`, () => {
    test.beforeEach(({ registerApiResponse }) => {
        const modelSource = { model_id: 'model-id', model_storage_id: 'model-storage-id', user_id: null };

        registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
            return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });
        registerApiResponse('GetSinglePrediction', (req, res, ctx) => {
            const roi = req.query.roi;
            const detectionModelId = '635fce72fc03e87df9becd10';
            const isDetection = req.params.pipeline_id === detectionModelId;

            const newPredictions = predictions
                .map((annotation) => {
                    const labels = annotation.labels.map((label) => ({
                        ...label,
                        probability: Math.random(),
                        source: modelSource,
                    }));
                    return { ...annotation, labels };
                })
                .filter((annotation) => {
                    if (isDetection) {
                        return annotation.labels.some(isAnimalLabel);
                    }

                    if (roi === undefined) {
                        return true;
                    }

                    return !annotation.labels.some((label) => {
                        return detectionLabels.some(({ id }) => id === label.id);
                    });
                });

            return res(ctx.json({ predictions: newPredictions }));
        });
    });

    test.describe('Replacing empty user annotations with predictions', () => {
        test.beforeEach(({ registerApiResponse }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
            });
        });

        test('All tasks: using online predictions', async ({ page, registerApiResponse }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(annotatorUrl);

            await replaceAnnotationsByPredictions(page);

            await getSubmitButton(page).click();
            expect(storedAnnotations).toHaveLength(1);
            expect(storedAnnotations[0]).toHaveLength(predictions.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(annotation.shape).toEqual(predictions[index].shape);
                expect(getIds(annotation.labels)).toEqual(getIds(predictions[index].labels));
            });
        });

        test('Detection: using online predictions', async ({ page, registerApiResponse }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);
            await page.goto(`${annotatorUrl}?task-id=${detectionId}`);
            await replaceAnnotationsByPredictions(page);

            await getSubmitButton(page).click();
            expect(storedAnnotations).toHaveLength(1);
            const predictedAnimals = predictions.filter(({ labels }) => labels.some(isAnimalLabel));
            expect(storedAnnotations[0]).toHaveLength(predictedAnimals.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(annotation.shape).toEqual(predictedAnimals[index].shape);
                expect(getIds(annotation.labels)).toEqual(getIds(predictedAnimals[index].labels));
            });
        });

        test('Segmentation: no user annotations / inputs', async ({ page }) => {
            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
            await expectSubmitToBeEnabled(page);

            await expect(page.getByRole('link', { name: 'Go to detection' })).toBeVisible();
            await expect(
                page
                    .locator('#custom-notification div')
                    .getByText('Nothing to segment. Draw bounding boxes on objects for segmentation.')
            ).toBeVisible();
        });

        test('Segmentation: user annotations for detection task, predictions for segmentation', async ({
            page,
            registerApiResponse,
        }) => {
            const inputAnnotations = annotations.filter(filterInputs);
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(ctx.json({ ...userAnnotationsResponse, annotations: inputAnnotations }));
            });

            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
            await expectSubmitToBeEnabled(page);

            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 1].id
            );

            // Let's verify that the annotation status of each input is updated
            const submitButton = getSubmitButton(page);
            await submitButton.click();

            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 2].id
            );

            expect(storedAnnotations).toHaveLength(1);
            expect(storedAnnotations[0]).toHaveLength(inputAnnotations.length + 1);

            await submitButton.click();

            expect(storedAnnotations).toHaveLength(2);
            expect(storedAnnotations[1]).toHaveLength(inputAnnotations.length + 2);

            await submitButton.click();

            expect(storedAnnotations).toHaveLength(3);
            expect(storedAnnotations[2]).toHaveLength(inputAnnotations.length + 3);

            await submitButton.click();

            // The last input has 2 outputs
            expect(storedAnnotations).toHaveLength(4);
            expect(storedAnnotations[3]).toHaveLength(inputAnnotations.length + 5);

            // After submitting the last input we should go to the next image
            await expectSubmitToBeEnabled(page);
            expect(page.url()).not.toEqual(`${annotatorUrl}?task-id=${segmentationId}`);
        });

        test('Segmentation: It does not load predictions when the user is drawing annotations', async ({
            page,
            registerApiResponse,
            boundingBoxTool,
        }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: annotations.filter(filterInputs) }))
            );

            const timeout = 1500;
            registerApiResponse('GetSinglePrediction', async (req, res, ctx) => {
                const roi = req.query.roi;
                const source = { model_id: 'model-id', model_storage_id: 'model-storage-id', user_id: null };

                const newPredictions = predictions
                    .map((annotation) => {
                        const labels = annotation.labels.map((label) =>
                            label.id === animalLabelId ? label : { ...label, probability: Math.random(), source }
                        );
                        return { ...annotation, labels };
                    })
                    .filter((annotation) => {
                        if (roi === undefined) {
                            return true;
                        }

                        return !annotation.labels.some((label) => {
                            return detectionLabels.some(({ id }) => id === label.id);
                        });
                    });

                await delay(timeout);

                return res(ctx.json({ predictions: newPredictions }));
            });

            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);

            await page.waitForTimeout(timeout);
            const deerPredictionRegex = /^deer \d+%$/; // "deer 51%'
            await expectAnnotationVisible(page, deerPredictionRegex);

            await page.reload();
            // Draw a bounding box and make sure it is not overwritten by the system's predictions
            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox({ x: 45, y: 115, width: 60, height: 50 });

            await page.waitForTimeout(timeout);
            const annotationsLabelsContainer = page
                .getByLabel('annotations', { exact: true })
                .getByRole('list', { name: 'labels' });

            await expect(annotationsLabelsContainer).toHaveCount(0);
        });

        test('Segmentation: inputs with overlap containing outputs', async ({ page, registerApiResponse }) => {
            const inputAnnotations = predictions.filter(filterInputs);
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(ctx.json({ ...userAnnotationsResponse, annotations: inputAnnotations }));
            });

            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
            await expectSubmitToBeEnabled(page);

            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 1].id
            );
            // The last input is overlapping and also contains this input's outputs
            await expectToHaveAnnotationInputWithAnnotatedStatus(page, inputAnnotations[0].id);

            // Let' verify that the annotation status of each input is updated
            const submitButton = getSubmitButton(page);
            await submitButton.click();

            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 2].id
            );

            expect(storedAnnotations).toHaveLength(1);
            expect(storedAnnotations[0]).toHaveLength(predictions.filter(filterInputs).length + 1);

            await submitButton.click();

            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 3].id
            );

            expect(storedAnnotations).toHaveLength(2);
            expect(storedAnnotations[1]).toHaveLength(predictions.filter(filterInputs).length + 2);

            await submitButton.click();
            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 4].id
            );

            expect(storedAnnotations).toHaveLength(3);
            expect(storedAnnotations[2]).toHaveLength(predictions.filter(filterInputs).length + 3);

            await submitButton.click();
            await expectToHaveAnnotationInputWithAnnotatedStatus(
                page,
                inputAnnotations[inputAnnotations.length - 5].id
            );

            expect(storedAnnotations).toHaveLength(4);
            expect(storedAnnotations[3]).toHaveLength(predictions.filter(filterInputs).length + 4);

            // NOTE: currently we incorrectly decide not to show the output's annotations, because the
            // user previously opened an input overlapping this input. Thus we loaded an output for
            // this input into the user's scene.
            await replaceAnnotationsByPredictions(page);

            await getSubmitButton(page).click();
            expect(storedAnnotations).toHaveLength(5);
            expect(storedAnnotations[4]).toHaveLength(predictions.filter(filterInputs).length + 5);

            await expectSubmitToBeEnabled(page);
            expect(page.url()).not.toEqual(`${annotatorUrl}?task-id=${segmentationId}`);
        });

        test('It submits a predicted empty annotation', async ({ page, registerApiResponse }) => {
            // Setup annotations and predictions so that we only have input annotations,
            // in addition the prediction always returns the "emtpy" label
            const emptySegmentationLabel = segmentationLabels[1];
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(
                    ctx.json({
                        ...userAnnotationsResponse,
                        annotations: predictions.filter((annotation) => {
                            return annotation.labels.some(isAnimalLabel);
                        }),
                    })
                );
            });

            const source = {
                model_id: 'model-id',
                model_storage_id: 'model-storage-id',
                user_id: null,
            };

            const emptyPredictions = predictions
                .map((annotation) => {
                    const labels = annotation.labels.map((label) =>
                        label.id === animalLabelId ? label : { ...label, probability: Math.random(), source }
                    );
                    return {
                        ...annotation,
                        labels: [
                            ...labels,
                            { ...labels[0], id: emptySegmentationLabel.id, probability: Math.random(), source },
                        ],
                    };
                })
                .filter((annotation) => {
                    return annotation.labels.some(isAnimalLabel);
                });

            registerApiResponse('GetSinglePrediction', (req, res, ctx) => {
                const roi = req.query.roi;

                // TODO: rewrite these into simpler forms
                const newPredictions = emptyPredictions.filter(({ shape }) => {
                    if (roi === undefined) {
                        return true;
                    }

                    const [x, y, width, height] = roi.split(',');

                    return (
                        shape.type === SHAPE_TYPE_DTO.RECTANGLE &&
                        shape.x === Number(x) &&
                        shape.y === Number(y) &&
                        shape.width === Number(width) &&
                        shape.height === Number(height)
                    );
                });

                return res(ctx.json({ predictions: newPredictions }));
            });

            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
            await expectSubmitToBeEnabled(page);

            await getSubmitButton(page).click();
            await expectSubmitToBeEnabled(page);

            expect(storedAnnotations).toHaveLength(1);
            expect(
                storedAnnotations[0][4].labels.find((label) => label.id === emptySegmentationLabel.id)
            ).not.toBeUndefined();
        });
    });

    test.describe('Using auto predictions', () => {
        test.beforeEach(({ registerApiResponse }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
            });
        });

        test('All tasks: accepting auto predictions', async ({ page, registerApiResponse }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(annotatorUrl);
            await expectSubmitToBeEnabled(page);

            const submitButton = getSubmitButton(page);
            await submitButton.click();

            expect(storedAnnotations).toHaveLength(1);
            expect(storedAnnotations[0]).toHaveLength(predictions.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(annotation.shape).toEqual(predictions[index].shape);
                expect(getIds(annotation.labels)).toEqual(getIds(predictions[index].labels));
            });
        });

        test('Detection: accepting auto predictions', async ({ page, registerApiResponse }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(`${annotatorUrl}?task-id=${detectionId}`);
            await expectSubmitToBeEnabled(page);

            const submitButton = getSubmitButton(page);
            await submitButton.click();

            expect(storedAnnotations).toHaveLength(1);
            const predictedAnimals = predictions.filter(({ labels }) => labels.some(isAnimalLabel));
            expect(storedAnnotations[0]).toHaveLength(predictedAnimals.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(annotation.shape).toEqual(predictedAnimals[index].shape);
                expect(getIds(annotation.labels)).toEqual(getIds(predictedAnimals[index].labels));
            });
        });
    });

    test.describe('With user annotations', () => {
        test.fixme(
            'Segmentation: mix loading user annotations and predictions',
            async ({ page, registerApiResponse }) => {
                const userAnnotations = annotations.filter((annotation, index) => {
                    if (annotation.labels[0].id === deerLabelId) {
                        return [8, 7, 6].includes(index);
                    }
                    return true;
                });
                registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                    return res(
                        ctx.json({
                            ...userAnnotationsResponse,
                            annotations: userAnnotations,
                        })
                    );
                });
                registerApiResponse('GetSinglePrediction', (req, res, ctx) => {
                    const isDetection = req.params.task_id === detectionId;

                    const newPredictions = predictions
                        .map((annotation) => {
                            const source = {
                                model_id: 'model-id',
                                model_storage_id: 'model-storage-id',
                                user_id: null,
                            };
                            const labels = annotation.labels.map((label) =>
                                label.id === animalLabelId ? label : { ...label, probability: Math.random(), source }
                            );
                            return { ...annotation, labels };
                        })
                        .filter((annotation) => {
                            if (isDetection) {
                                return annotation.labels.some(isAnimalLabel);
                            }

                            return true;
                        });

                    return res(ctx.json({ predictions: newPredictions }));
                });
                const storedAnnotations = registerStoreAnnotations(registerApiResponse);

                const inputAnnotations = annotations.filter(filterInputs);
                await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
                await expectSubmitToBeEnabled(page);

                await page
                    .getByTestId(`annotation-${inputAnnotations[inputAnnotations.length - 2].id}-thumbnail`)
                    .click();
                await expect
                    .soft(async () => {
                        await expectNotToHaveAnnotationInputWithAnnotatedStatus(
                            page,
                            inputAnnotations[inputAnnotations.length - 1].id
                        );
                    })
                    .toPass({ timeout: 1000 });

                await page
                    .getByTestId(`annotation-${inputAnnotations[inputAnnotations.length - 3].id}-thumbnail`)
                    .click();
                await expect
                    .soft(async () => {
                        await expectNotToHaveAnnotationInputWithAnnotatedStatus(
                            page,
                            inputAnnotations[inputAnnotations.length - 2].id
                        );
                    })
                    .toPass({ timeout: 1000 });

                const submitButton = getSubmitButton(page);
                await submitButton.click();

                // The user did not explicitly accept the previous predictions, so we should
                // not be submitting any annotations
                expect(storedAnnotations).toHaveLength(0);

                await page
                    .getByTestId(`annotation-${inputAnnotations[inputAnnotations.length - 3].id}-thumbnail`)
                    .click();
                await submitButton.click();

                // Now we did submit one of the predictions, and we expect that only the user's
                // annotations and the accepted annotations are stored
                expect(storedAnnotations).toHaveLength(1);
                expect(storedAnnotations[0]).toHaveLength(userAnnotations.length + 1);
            }
        );

        test.fixme(
            'Detection: A confirmation message is shown when deleting a detection input that has outputs',
            async ({ page, annotationListPage, registerApiResponse }) => {
                registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                    return res(ctx.json({ ...userAnnotationsResponse, annotations }));
                });

                const storedAnnotations = registerStoreAnnotations(registerApiResponse);

                const inputAnnotations = annotations.filter(filterInputs);
                await page.goto(`${annotatorUrl}?task-id=${detectionId}`);
                await expectSubmitToBeEnabled(page);

                const listItem = await annotationListPage.getAnnotationListItem(
                    page.getByRole('listitem', { name: new RegExp(inputAnnotations[0].id) })
                );
                await listItem.select();

                // FIXME: here we should ask the user if they are certain they want to remove this annotation
                await annotationListPage.removeSelected();

                await getSubmitButton(page).click();
                await expectSubmitToBeEnabled(page);

                // The input annotation should be removed, but also its output
                expect(storedAnnotations[0]).toHaveLength(annotations.length - 2);
            }
        );
    });

    test.describe('All tasks', () => {
        test('No annotations, no predictions', async ({ page, registerApiResponse }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
            );
            registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));

            await page.goto(annotatorUrl);

            await expect(page.getByLabel('annotations').locator(`id=${predictionAnnotationId}-labels`)).toBeHidden();
            await expect(page.getByLabel('annotations').locator(`id=${userAnnotationId}-labels`)).toBeHidden();

            await expect(page.getByLabel('annotations').getByLabel('labels')).toBeHidden();

            await page.getByPlaceholder('Select default label').click();

            // Check that the default label allows selecting all the project's labels
            const labelSearch = page.getByLabel('Label search results');
            await expect(labelSearch).toBeVisible();
            await expect(labelSearch.getByRole('listitem', { name: /deer/i })).toBeVisible();
            await expect(labelSearch.getByRole('listitem', { name: /animal/i })).toBeVisible();
        });

        test('All task', async ({ page, annotationListPage, registerApiResponse }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(annotatorUrl);
            await expect(getSubmitButton(page)).toBeVisible();

            await annotationListPage.expectTotalAnnotationsToBe(predictions.length);

            await getSubmitButton(page).click();
            expect(storedAnnotations).toHaveLength(1);
            expect(storedAnnotations[0]).toHaveLength(predictions.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(annotation.shape).toEqual(predictions[index].shape);
                expect(getIds(annotation.labels)).toEqual(getIds(predictions[index].labels));
            });
        });

        test('Annotator page elements', async ({ page, registerApiExample }) => {
            registerApiExample('GetProjectStatus', 'Waiting for classification annotations');

            await page.goto(annotatorUrl);

            await expect(page.getByRole('navigation', { name: 'navigation-breadcrumbs' })).toBeVisible();
            await expect(page.locator('[id=breadcrumb-all-tasks]')).toBeVisible({ timeout: 5000 });
            await expect(page.locator('[id="breadcrumb-Detection"]')).toBeVisible();
            await expect(page.locator('[id="breadcrumb-Segmentation"]')).toBeVisible();

            await checkNumberOfTools(page, 8);

            await checkCommonElements(page, DOMAIN.SEGMENTATION);
        });
    });

    test.describe('Detection', () => {
        test('Detection', async ({ page, annotationListPage, registerApiResponse }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);
            await page.goto(`${annotatorUrl}?task-id=635fce72fc03e87df9becd10`);

            const detectionPredictions = predictions.filter((annotation) => {
                return annotation.labels.some(isAnimalLabel);
            });

            await expect(getSubmitButton(page)).toBeVisible();

            await expect(page.getByRole('button', { name: 'filter-by-score-button' })).toBeVisible();
            await annotationListPage.expectTotalAnnotationsToBe(detectionPredictions.length);

            await getSubmitButton(page).click();

            expect(storedAnnotations).toHaveLength(1);

            expect(storedAnnotations[0]).toHaveLength(detectionPredictions.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(annotation.shape).toEqual(detectionPredictions[index].shape);
                expect(getIds(annotation.labels)).toEqual(getIds(detectionPredictions[index].labels));
            });
        });

        test.fixme(
            'Switching to detection and submitting predictions only submits detection annotations',
            async ({ page, annotationListPage, registerApiResponse }) => {
                const storedAnnotations = registerStoreAnnotations(registerApiResponse);
                await page.goto(annotatorUrl);

                const detectionPredictions = predictions.filter((annotation) => {
                    return annotation.labels.some(isAnimalLabel);
                });

                await expect(getSubmitButton(page)).toBeVisible();
                await goToDetection(page);

                await expect(page.getByRole('button', { name: 'filter-by-score-button' })).toBeVisible();
                await annotationListPage.expectTotalAnnotationsToBe(detectionPredictions.length);

                await getSubmitButton(page).click();

                expect(storedAnnotations).toHaveLength(1);

                // BUG: when going to detection we do not discard segmentation predictiosn
                expect(storedAnnotations[0]).toHaveLength(detectionPredictions.length);
                storedAnnotations[0].forEach((annotation, index) => {
                    expect(annotation.shape).toEqual(detectionPredictions[index].shape);
                    expect(getIds(annotation.labels)).toEqual(getIds(detectionPredictions[index].labels));
                });
            }
        );
    });

    test.describe('Segmentation', () => {
        test('Segmentation - single roi', async ({ page, registerApiResponse, annotationListPage }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: [annotations[0]] }))
            );

            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
            await expect(getSubmitButton(page)).toBeVisible();

            await expect(page.getByRole('button', { name: 'filter-by-score-button' })).toBeVisible();
            await annotationListPage.expectTotalAnnotationsToBe(2);

            await getSubmitButton(page).click();

            expect(storedAnnotations).toHaveLength(1);
            const expectedStoredAnnotations = [annotations[0], predictions[7], predictions[8]];

            expect(storedAnnotations[0]).toHaveLength(expectedStoredAnnotations.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(getIds(annotation.labels)).toEqual(getIds(expectedStoredAnnotations[index].labels));
                expect(annotation.shape).toEqual(expectedStoredAnnotations[index].shape);
            });
        });

        test('Segmentation - multiple rois', async ({ page, registerApiResponse, annotationListPage }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: [annotations[1], annotations[0]] }))
            );

            await page.goto(`${annotatorUrl}?task-id=${segmentationId}`);
            await expect(getSubmitButton(page)).toBeVisible();

            await annotationListPage.expectTotalAnnotationsToBe(2);
            await getSubmitButton(page).click();

            const expectedStoredAnnotations = [annotations[1], annotations[0], predictions[7], predictions[8]];
            expect(storedAnnotations[0]).toHaveLength(expectedStoredAnnotations.length);
            storedAnnotations[0].forEach((annotation, index) => {
                expect(getIds(annotation.labels)).toEqual(getIds(expectedStoredAnnotations[index].labels));
                expect(annotation.shape).toEqual(expectedStoredAnnotations[index].shape);
            });

            await annotationListPage.expectTotalAnnotationsToBe(1);
            await annotationListPage.expectTotalAnnotationsToBe(1);

            await getSubmitButton(page).click();

            const expectedStoredAnnotations2 = [
                annotations[1],
                annotations[0],
                predictions[7],
                predictions[8],
                predictions[4],
            ];
            expect(storedAnnotations[1]).toHaveLength(expectedStoredAnnotations2.length);
            storedAnnotations[1].forEach((annotation, index) => {
                expect(getIds(annotation.labels)).toEqual(getIds(expectedStoredAnnotations2[index].labels));
                expect(annotation.shape).toEqual(expectedStoredAnnotations2[index].shape);
            });
        });

        test('Regression Detection -> Segmentation', async ({ page, registerApiResponse }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(
                    ctx.json({
                        ...userAnnotationsResponse,
                        annotations: annotations.filter((annotation, index) => {
                            if (annotation.labels[0].id === deerLabelId) {
                                return [5, 6].includes(index);
                            }
                            return true;
                        }),
                    })
                );
            });

            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(`${annotatorUrl}?task-id=635fce72fc03e87df9becd12`);
            await expectSubmitToBeEnabled(page);

            await getSubmitButton(page).click();

            await getSubmitButton(page).click();

            expect(storedAnnotations).toHaveLength(1);
            await expectSubmitToBeEnabled(page);
            expect(page.url()).toContain(`${annotatorUrl}?task-id=635fce72fc03e87df9becd12`);
        });
    });

    test.describe('task navigation', () => {
        test('All task => Detection => Segmentation', async ({ page, registerApiResponse }) => {
            const initialAnnotations = annotations.filter((annotation, index) => {
                if (annotation.labels[0].id === deerLabelId) {
                    return [6, 7].includes(index);
                }
                return true;
            });

            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                return res(ctx.json({ ...userAnnotationsResponse, annotations: initialAnnotations }));
            });

            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(annotatorUrl);
            await expect(getSubmitButton(page)).toBeVisible();

            await goToDetection(page);
            const detectionIds = getIds(annotations.filter((annotation) => annotation.labels.some(isAnimalLabel)));
            await Promise.all(detectionIds.map((id) => expectAnnotationIsVisible(page, id, detectionLabels[0].name)));

            await goToSegmentation(page);
            await getSubmitButton(page).click();

            expect(storedAnnotations).toHaveLength(1);
            expect(storedAnnotations[0]).toHaveLength(initialAnnotations.length + 1);
        });
    });

    test.describe('active learning mode', () => {
        test('overlap annotations with annotation selection', async ({ page, registerApiResponse }) => {
            const detectionAnnotation = userAnnotationsResponse.annotations[0];
            const predictionSegmentation = predictionAnnotationsResponse.annotations[1];

            const annotationsSegmentation = {
                ...predictionSegmentation,
                labels: setToUserId(predictionSegmentation.labels),
            };

            const segmentationPredictions = [predictionAnnotationsResponse.annotations[1]];
            registerApiResponse('GetSinglePrediction', (_, res, ctx) =>
                res(ctx.json({ predictions: segmentationPredictions }))
            );
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(
                    ctx.json({
                        ...userAnnotationsResponse,
                        annotations: [detectionAnnotation, annotationsSegmentation],
                    })
                )
            );

            await page.goto(annotatorUrl);

            await goToSegmentation(page);

            await page.getByTestId('annotations-list-select-all').click();

            await page.getByRole('button', { name: 'Select prediction mode' }).click();

            const annotationContainer = page.getByLabel('annotations');
            const annotationsShapes = annotationContainer.locator('polygon');
            await expect(annotationsShapes).toHaveCount(segmentationPredictions.length);

            await page.getByRole('switch', { name: 'overlap annotations' }).click();
            await expect(annotationsShapes).toHaveCount(segmentationPredictions.length + 1);
        });

        test('replace annotation with predictions and render new annotations, bread crumb selection', async ({
            page,
            registerApiResponse,
        }) => {
            const userAnnotation = userAnnotationsResponse.annotations[0];
            const detectionPrediction = predictionAnnotationsResponse.annotations[0];
            const segmentationPrediction = predictionAnnotationsResponse.annotations[1];

            registerApiResponse('GetSinglePrediction', (_, res, ctx) =>
                res(ctx.json({ predictions: [detectionPrediction, segmentationPrediction] }))
            );
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: [userAnnotation] }))
            );
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            await page.goto(annotatorUrl);

            await expectAnnotationIsVisible(page, userAnnotation.id, userAnnotation.labels[0].name);

            await page.getByRole('button', { name: 'Select prediction mode' }).click();
            await page.getByRole('button', { name: 'Use predictions' }).click();

            await expect(page.getByText('Replace or merge annotations?')).toBeVisible();
            await page.getByRole('button', { name: /replace/i }).click();
            await page.getByRole('button', { name: 'Select annotation mode' }).click();

            await goToDetection(page);
            await page.getByRole('button', { name: /submit/i }).click();

            await goToAllTask(page);

            expect(storedAnnotations[0]).toEqual(
                expect.arrayContaining([
                    expect.objectContaining({
                        shape: detectionPrediction.shape,
                    }),
                    expect.objectContaining({
                        shape: segmentationPrediction.shape,
                    }),
                ])
            );
        });

        test('cancel slow "/predictions/auto" request after 60s', async ({
            page,
            registerApiResponse,
            annotationListPage,
        }) => {
            const responseTimeout = 60_000;
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
            );

            registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
                await delay(responseTimeout + 1);
                return res(ctx.json({ predictions: predictionAnnotationsResponse.annotations }));
            });

            await page.goto(annotatorUrl);

            await page.waitForTimeout(responseTimeout);

            await annotationListPage.expectTotalAnnotationsToBe(0);
        });
    });

    test.describe('prediction as annotations config', () => {
        test.beforeEach(({ registerApiResponse }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json({ ...userAnnotationsResponse })));
            registerApiResponse('GetSinglePrediction', (req, res, ctx) => {
                const roi = req.query.roi;
                const detectionModelId = '635fce72fc03e87df9becd10';
                const isDetection = req.params.pipeline_id === detectionModelId;
                const source = { model_id: 'model-id', model_storage_id: 'model-storage-id', user_id: null };

                const newPredictions = predictionAnnotationsResponse.annotations
                    .map((annotation) => {
                        const labels = annotation.labels.map((label) => ({
                            ...label,
                            probability: Math.random(),
                            source,
                        }));
                        return { ...annotation, labels };
                    })
                    .filter((annotation) => {
                        if (isDetection) {
                            return annotation.labels.some(isAnimalLabel);
                        }

                        if (roi === undefined) {
                            return true;
                        }

                        return !annotation.labels.some((label) => {
                            return detectionLabels.some(({ id }) => id === label.id);
                        });
                    });

                return res(ctx.json({ predictions: newPredictions }));
            });
        });

        test('enable initial prediction as annotations', async ({ page, registerApiResponse, annotationListPage }) => {
            const storedAnnotations = registerStoreAnnotations(registerApiResponse);

            registerStoreSettings(registerApiResponse, JSON.parse(settings));
            await page.goto(annotatorUrl);
            await toggleShowPredictions(page, true);

            await goToSegmentation(page);

            await expect(page.getByRole('button', { name: 'filter-by-score-button' })).toBeVisible();
            await annotationListPage.expectTotalAnnotationsToBe(1);
            await getSubmitButton(page).click();

            expect(storedAnnotations).toHaveLength(1);

            await page.getByTestId(`annotation-${userAnnotationId}-thumbnailWrapper`).click();
            await annotationListPage.expectTotalAnnotationsToBe(1);
            await getSubmitButton(page).click();

            expect(storedAnnotations).toHaveLength(2);
            expect(storedAnnotations[0]).toHaveLength(3);
            expect(storedAnnotations[1]).toHaveLength(4);
        });

        test('disable initial predictions as annotations, not user annotations', async ({
            page,
            registerApiResponse,
        }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
            );

            registerStoreSettings(registerApiResponse);
            await page.goto(annotatorUrl);

            await toggleShowPredictions(page, false);
            await goToDetection(page);

            await page.getByRole('button', { name: /discard/i }).click();

            await expect(page.getByRole('button', { name: 'filter-by-score-button' })).toBeHidden();
            await expect(page.getByLabel('annotations', { exact: true }).getByLabel('labels')).toHaveCount(0);

            await goToDetection(page);
            await goToSegmentation(page);
            await goToAllTask(page);

            await expect(page.getByText('Discard or submit annotations')).toBeHidden();
        });

        test('disable initial predictions as annotations, discard/submit modal is hidden', async ({
            page,
            registerApiResponse,
        }) => {
            registerStoreSettings(registerApiResponse);
            await page.goto(annotatorUrl);
            await toggleShowPredictions(page, false);

            await goToSegmentation(page);
            await expect(page.getByLabel('annotations', { exact: true }).getByLabel('labels')).toHaveCount(0);

            await page.getByTestId(`annotation-${userAnnotationId}-thumbnailWrapper`).click();
            await expect(page.getByText('Discard or submit annotations')).toBeHidden();
            await expect(page.getByLabel('annotations', { exact: true }).getByLabel('labels')).toHaveCount(0);

            await goToAllTask(page);
            await expect(page.getByText('Discard or submit annotations')).toBeHidden();
        });
    });

    test.describe('prediction mode', () => {
        test('All Task, Slow "/predictions/online" request is not cancel', async ({ page, registerApiResponse }) => {
            const responseTimeout = 5000;

            registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
                await delay(responseTimeout + 1);
                return res(ctx.json({ predictions }));
            });

            await page.goto(`${annotatorUrl}?mode=prediction`);

            await page.waitForTimeout(responseTimeout + 100);

            await expect(page.getByLabel('annotations', { exact: true }).getByLabel('labels')).toHaveCount(
                predictions.length
            );
        });
    });
});
