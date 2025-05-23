// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { test } from '../../fixtures/base-test';

import '../../mocks/detection-segmentation/mocks';

import { BarChartPage, ObjectSizeDistributionChartPage } from '../../fixtures/page-objects/chart-pages';
import { DatasetStatisticsPage } from '../../fixtures/page-objects/dataset-statistics-page';
import { expectCSVToBeEqual, expectToBeDownloaded } from '../../utils/expects';
import { getMedia } from '../annotator/navigation/mocks';
import {
    datasetStatistics,
    detectionStatistics,
    segmentationStatistics,
    taskChainDetectionSegmentationProject,
} from './mocks';

type Statistics = typeof detectionStatistics;

const expectNumberOfObjectsPerLabelToBeVisible = async (
    objectsPerLabel: Statistics['objects_per_label'],
    barChart: BarChartPage
) => {
    for (const label of objectsPerLabel) {
        await expect(barChart.getColumn(label.name)).toHaveAttribute('aria-valuenow', label.value.toString());
    }
};

const expectObjectDistributionToBeVisible = async (
    objectsPerLabel: Statistics['object_size_distribution_per_label'],
    objectSizeDistributionChartPage: ObjectSizeDistributionChartPage
) => {
    for (const objectClass of objectsPerLabel) {
        await objectSizeDistributionChartPage.selectObjectClass(objectClass.name);
        await expect(objectSizeDistributionChartPage.getNumberOfObjects()).toContainText(
            objectClass.size_distribution.length.toString()
        );
    }
};

const expectStatisticsToBeVisible = async (
    {
        images,
        videos,
        annotated_images,
        annotated_videos,
        annotated_frames,
        object_size_distribution_per_label,
        objects_per_label,
    }: Statistics,
    datasetStatisticsPage: DatasetStatisticsPage
) => {
    await expect(datasetStatisticsPage.getImagesCount()).toContainText(images.toString());
    await expect(datasetStatisticsPage.getVideosCount()).toContainText(videos.toString());
    await expect(datasetStatisticsPage.getAnnotatedImagesCount()).toContainText(annotated_images.toString());
    await expect(datasetStatisticsPage.getAnnotatedImagesProgressbar()).toHaveAttribute(
        'aria-valuetext',
        `${(annotated_images / images) * 100}%`
    );
    await expect(datasetStatisticsPage.getAnnotatedVideosCount()).toContainText(annotated_videos.toString());
    await expect(datasetStatisticsPage.getAnnotatedFramesCount()).toContainText(annotated_frames.toString());

    const barChart = datasetStatisticsPage.getBarChart('Number of objects per label');
    await expectNumberOfObjectsPerLabelToBeVisible(objects_per_label, barChart);

    await expectToBeDownloaded(datasetStatisticsPage.getPage(), () => barChart.downloadPDF());

    await barChart.openFullScreen();

    const barChartInFullScreen = datasetStatisticsPage.getFullScreenBarChart('Number of objects per label');
    await expectNumberOfObjectsPerLabelToBeVisible(objects_per_label, barChartInFullScreen);
    await expectToBeDownloaded(datasetStatisticsPage.getPage(), () => barChartInFullScreen.downloadPDF());
    await barChartInFullScreen.closeFullScreen();

    const objectSizeDistribution = datasetStatisticsPage.getObjectSizeDistributionChart();
    await expectObjectDistributionToBeVisible(object_size_distribution_per_label, objectSizeDistribution);
    await expectToBeDownloaded(datasetStatisticsPage.getPage(), () => objectSizeDistribution.downloadPDF());

    await expectToBeDownloaded(datasetStatisticsPage.getPage(), () => datasetStatisticsPage.downloadAll());
};

const expectObjectDistributionSizeToBeEqualCSV = async (
    objectsSizeDistributions: Statistics['object_size_distribution_per_label'],
    datasetStatisticsPage: DatasetStatisticsPage
) => {
    const objectSizeDistributionChartPage = datasetStatisticsPage.getObjectSizeDistributionChart();

    for (const objectSizeDistribution of objectsSizeDistributions) {
        await objectSizeDistributionChartPage.selectObjectClass(objectSizeDistribution.name);

        const expectedObjectSizeDistributionContent = objectSizeDistribution.size_distribution.reduce(
            (allObjectsSizeDistributions, current) => {
                const [width, height] = current;

                allObjectsSizeDistributions.push([width.toString(), height.toString()]);
                return allObjectsSizeDistributions;
            },
            [['Width', 'Height']] as string[][]
        );

        const objectSizeDistributionCSV = await objectSizeDistributionChartPage.downloadAndReadCSV();

        expectCSVToBeEqual(objectSizeDistributionCSV, expectedObjectSizeDistributionContent);
    }
};

const expectNumberOfObjectsPerLabelToBeEqualCSV = (expected: Statistics['objects_per_label'], actual: string[][]) => {
    const expectedObjectsPerLabelCSV = expected.reduce(
        (objectsPerLabel, current) => {
            objectsPerLabel[0].push(current.name);
            objectsPerLabel[1].push(current.value.toString());

            return objectsPerLabel;
        },
        [[], []] as string[][]
    );

    expectCSVToBeEqual(expectedObjectsPerLabelCSV, actual);
};

test.describe('Dataset statistics', () => {
    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(taskChainDetectionSegmentationProject)));
        registerApiResponse('GetDatasetStatistics', (req, res, ctx) => {
            const taskId = (req.query.task_id ?? '4dc8f244b7bfafc65898ed2a') as keyof typeof datasetStatistics;
            const datasetStatisticsPerTask = datasetStatistics[taskId];

            return res(ctx.json(datasetStatisticsPerTask));
        });
    });

    test('Displays and downloads dataset statistics', async ({ datasetStatisticsPage, registerApiResponse }) => {
        registerApiResponse('FilterMedia', (_, res, ctx) => {
            return res(
                ctx.json({
                    media: [getMedia('1'), getMedia('2'), getMedia('3'), getMedia('4')],
                    total_matched_images: 4,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: 4,
                    total_videos: 0,
                })
            );
        });

        await datasetStatisticsPage.openByURL();

        await datasetStatisticsPage.selectTask('Segmentation');

        await expectStatisticsToBeVisible(segmentationStatistics, datasetStatisticsPage);

        await datasetStatisticsPage.selectTask('Detection');

        await expectStatisticsToBeVisible(detectionStatistics, datasetStatisticsPage);
    });

    test('Downloads CSV with statistics', async ({ datasetStatisticsPage, registerApiResponse }) => {
        registerApiResponse('FilterMedia', (_, res, ctx) => {
            return res(
                ctx.json({
                    media: [getMedia('1'), getMedia('2'), getMedia('3'), getMedia('4')],
                    total_matched_images: 4,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: 4,
                    total_videos: 0,
                })
            );
        });

        await datasetStatisticsPage.openByURL();

        await datasetStatisticsPage.selectTask('Segmentation');

        const barChartSegmentation = datasetStatisticsPage.getBarChart('Number of objects per label');
        const numberOfObjectPerLabelCSVSegmentation = await barChartSegmentation.downloadAndReadCSV();

        expectNumberOfObjectsPerLabelToBeEqualCSV(
            segmentationStatistics.objects_per_label,
            numberOfObjectPerLabelCSVSegmentation
        );

        await expectObjectDistributionSizeToBeEqualCSV(
            segmentationStatistics.object_size_distribution_per_label,
            datasetStatisticsPage
        );

        await datasetStatisticsPage.selectTask('Detection');

        const barChartDetection = datasetStatisticsPage.getBarChart('Number of objects per label');
        const numberOfObjectPerLabelCSVDetection = await barChartDetection.downloadAndReadCSV();

        expectNumberOfObjectsPerLabelToBeEqualCSV(
            detectionStatistics.objects_per_label,
            numberOfObjectPerLabelCSVDetection
        );

        await expectObjectDistributionSizeToBeEqualCSV(
            detectionStatistics.object_size_distribution_per_label,
            datasetStatisticsPage
        );
    });

    test('Redirects to media page when the dataset is empty', async ({
        registerApiResponse,
        datasetStatisticsPage,
        datasetPage,
        page,
    }) => {
        registerApiResponse('FilterMedia', (_, res, ctx) => {
            return res(
                ctx.json({
                    media: [],
                    total_matched_images: 0,
                    total_matched_videos: 0,
                    total_matched_video_frames: 0,
                    total_images: 0,
                    total_videos: 0,
                })
            );
        });

        await datasetStatisticsPage.openByURL();

        await expect(page).not.toHaveURL(/statistics/);
        await expect(page).toHaveURL(/media/);

        await expect(datasetPage.getMediaTab()).toHaveAttribute('aria-selected', 'true');
        await expect(datasetPage.getStatisticsTab()).toHaveAttribute('aria-selected', 'false');
    });
});
