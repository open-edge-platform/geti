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

import { expect, Page } from '@playwright/test';

import { idMatchingFormat } from '../../../../src/test-utils/id-utils';
import { test } from '../../../fixtures/base-test';
import { OpenApiFixtures } from '../../../fixtures/open-api';
import { hierarchicalLabelsProject, multiLabelProject, singeLabelProject } from '../../../mocks/classification/mocks';
import { videoAnnotations } from '../anomaly/anomaly-video-ranges/mocks';
import { RangesRowType, VideoRangePage } from '../utils';

const datasetUrl =
    // eslint-disable-next-line max-len
    '/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/6290a8f9003ddb3967f14385/datasets/639757d00d117eb552d21300';

const videoMediaItem = {
    id: '613a23866674c43ae7a777ab',
    media_information: {
        display_url:
            // eslint-disable-next-line max-len
            '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61376cf8c0e392f0c4efb2bb/projects/6139eab61e3343cd22a41a66/datasets/6139eab61e3343cd22a41a65/media/videos/6139ec7555f78343bad38d2b/display/stream',
        duration: 30,
        frame_count: 901,
        frame_stride: 30,
        frame_rate: 30,
        height: 270,
        width: 480,
    },
    name: 'dummy_video',
    thumbnail:
        // eslint-disable-next-line max-len
        '/api/v1/organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61376cf8c0e392f0c4efb2bb/projects/6139eab61e3343cd22a41a66/datasets/6139eab61e3343cd22a41a65/media/images/613a23866674c43ae7a777ab/display/thumb',
    type: 'video',
    annotation_state_per_task: [
        {
            task_id: '61012cdb1d38a5e71ef3bafd',
            state: 'annotated',
        },
    ],
    upload_time: '2021-09-09T15:08:54.118000+00:00',
};

class ClassificationVideoRangesPage extends VideoRangePage {
    constructor(page: Page, rowId?: string) {
        super(page, rowId);
    }

    async unassignLabel() {
        const labelSearchResults = this.getLabelSearchResults();
        if (labelSearchResults) {
            await labelSearchResults.getByLabel('Assigned label').click();
        }
    }

    async assignLabel(label: string) {
        const labelSearchResults = this.getLabelSearchResults();
        if (labelSearchResults) {
            await labelSearchResults.getByText(label).click();
        }
    }

    async openLabelSearch(rangeIdx: number, row = this.defaultRow) {
        const range = this.getRanges(row).nth(rangeIdx);
        await range.click();
    }

    async clickRange(rangeIdx: number, row = this.defaultRow) {
        const range = this.getRanges(row).nth(rangeIdx);
        await range.click();
    }

    getRangesWithLabel(row: RangesRowType, label: string) {
        return this.getRangesRow(row).getByTestId(new RegExp(`${idMatchingFormat(label)}-range-section-id`));
    }

    getLabelAssigned(label: string) {
        return this.getLabel(label).getByLabel('Assigned label');
    }

    closeLabelSearch() {
        return this.page.mouse.click(0, 0);
    }
}

type ProjectType = Record<string, unknown>;

const setupBeforeEach =
    (project: ProjectType) =>
    async ({
        page,
        registerApiResponse,
    }: {
        page: Page;
        registerApiResponse: OpenApiFixtures['registerApiResponse'];
    }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('FilterMedia', (_, res, ctx) =>
            res(
                ctx.json({
                    media: [videoMediaItem],
                    total_images: 0,
                    total_matched_images: 0,
                    total_matched_videos: 1,
                    total_matched_videos_frames: 901,
                    total_videos: 1,
                })
            )
        );

        registerApiResponse('GetVideoAnnotationRange', (_, res, ctx) =>
            res(ctx.json({ range_labels: [{ start_frame: 0, end_frame: 900, label_ids: [] }] }))
        );

        registerApiResponse('GetVideoDetail', (_, res, ctx) => res(ctx.json(videoMediaItem)));
        registerApiResponse('GetVideoAnnotation', (_, res, ctx) => res(ctx.json(videoAnnotations)));

        await page.goto(datasetUrl);
        await page.locator('[class*=gridItem]').first().hover();
        await page.getByLabel('open menu').first().click();

        const videoRangePage = new ClassificationVideoRangesPage(page);

        await videoRangePage.openVideoRangeDialog();

        await expect(videoRangePage.videoRangeDialog).toBeVisible();
        await expect(videoRangePage.getVideoRangeDialogHeader()).toBeVisible();
    };

test.describe('Classification video ranges', () => {
    test.describe('Single label project', () => {
        test.beforeEach(setupBeforeEach(singeLabelProject));

        test('Creates video ranges', async ({ page }) => {
            const videoRangePage = new ClassificationVideoRangesPage(page, 'ranges-item-classification-labels-id');

            await expect(videoRangePage.getRangesRow(/ranges-item/)).toHaveCount(1);

            await videoRangePage.createRange(50, 200, 'suit');
            await videoRangePage.createRange(300, 400, 'value');
            await videoRangePage.createRange(350, 450, 'suit');

            await videoRangePage.changeLabel('value');

            // ranges created above + empty ranges between them
            await expect(videoRangePage.getRanges()).toHaveCount(6);

            const createRangesPromiseRequest = page.waitForRequest((req) => {
                return req.method() === 'POST' && req.url().endsWith('range_annotation');
            });

            await videoRangePage.saveRanges();

            await expect(videoRangePage.videoRangeDialog).toBeHidden();

            const createRangesRequest = await createRangesPromiseRequest;
            const bodyJSON = createRangesRequest.postData();
            const videoRanges = bodyJSON === null ? {} : JSON.parse(bodyJSON);

            expect(videoRanges.range_labels).toEqual([
                {
                    start_frame: 0,
                    end_frame: 26,
                    label_ids: ['66fead94117b329405566c0b'],
                },
                {
                    start_frame: 27,
                    end_frame: 121,
                    label_ids: ['66fead94117b329405566c0c'],
                },
                {
                    start_frame: 122,
                    end_frame: 182,
                    label_ids: [],
                },
                {
                    start_frame: 183,
                    end_frame: 214,
                    label_ids: ['66fead94117b329405566c0b'],
                },
                {
                    start_frame: 215,
                    end_frame: 277,
                    label_ids: ['66fead94117b329405566c0c'],
                },
                {
                    start_frame: 278,
                    end_frame: 900,
                    label_ids: [],
                },
            ]);
        });

        test('Assigns and unassigns labels for the given range', async ({ page }) => {
            const videoRangePage = new ClassificationVideoRangesPage(page, 'ranges-item-classification-labels-id');

            await videoRangePage.createRange(50, 200, 'suit');
            await videoRangePage.createRange(300, 400, 'value');
            await videoRangePage.createRange(350, 450, 'suit');

            await videoRangePage.openLabelSearch(1);
            await expect(videoRangePage.getLabelAssigned('suit')).toBeVisible();

            await videoRangePage.unassignLabel();

            await videoRangePage.openLabelSearch(1);
            await expect(videoRangePage.getLabelAssigned('suit')).toBeHidden();

            await videoRangePage.assignLabel('value');

            await videoRangePage.openLabelSearch(1);
            await expect(videoRangePage.getLabelAssigned('value')).toBeVisible();

            await expect(videoRangePage.getRangesWithLabel(videoRangePage.defaultRow, 'value')).toHaveCount(2);
            await expect(videoRangePage.getRangesWithLabel(videoRangePage.defaultRow, 'suit')).toHaveCount(1);
        });
    });

    test.describe('Multi label project', () => {
        test.beforeEach(setupBeforeEach(multiLabelProject));

        test('Creates video ranges', async ({ page }) => {
            const videoRangePage = new ClassificationVideoRangesPage(page);

            // One row per group, i.e. value, suit, no class.
            await expect(videoRangePage.getRangesRow(/ranges-item/)).toHaveCount(3);

            await videoRangePage.createRange(0, 200, 'suit', 'ranges-item-suit-id');
            await videoRangePage.createRange(50, 150, 'value', 'ranges-item-value-id');

            await videoRangePage.createRange(300, 450, 'suit', 'ranges-item-suit-id');
            await videoRangePage.createRange(350, 400, 'No class', 'ranges-item-no-class-id');

            await expect(videoRangePage.getRanges('ranges-item-suit-id')).toHaveCount(8);
            await expect(videoRangePage.getRanges('ranges-item-value-id')).toHaveCount(8);
            await expect(videoRangePage.getRanges('ranges-item-no-class-id')).toHaveCount(8);

            const createRangesPromiseRequest = page.waitForRequest((req) => {
                return req.method() === 'POST' && req.url().endsWith('range_annotation');
            });

            await videoRangePage.saveRanges();

            await expect(videoRangePage.videoRangeDialog).toBeHidden();

            const createRangesRequest = await createRangesPromiseRequest;
            const bodyJSON = createRangesRequest.postData();
            const videoRanges = bodyJSON === null ? {} : JSON.parse(bodyJSON);

            expect(videoRanges.range_labels).toEqual([
                {
                    start_frame: 0,
                    end_frame: 26,
                    label_ids: ['66fd3fe3b8fd1de60888602b'],
                },
                {
                    start_frame: 27,
                    end_frame: 90,
                    label_ids: ['66fd3fe3b8fd1de60888602b', '66fd3fe3b8fd1de60888602c'],
                },
                {
                    start_frame: 91,
                    end_frame: 121,
                    label_ids: ['66fd3fe3b8fd1de60888602b'],
                },
                {
                    start_frame: 122,
                    end_frame: 182,
                    label_ids: [],
                },
                {
                    start_frame: 183,
                    end_frame: 214,
                    label_ids: ['66fd3fe3b8fd1de60888602b'],
                },
                {
                    start_frame: 215,
                    end_frame: 246,
                    label_ids: ['66fd3fe3b8fd1de608886031'],
                },
                {
                    start_frame: 247,
                    end_frame: 277,
                    label_ids: ['66fd3fe3b8fd1de60888602b'],
                },
                {
                    start_frame: 278,
                    end_frame: 900,
                    label_ids: [],
                },
            ]);
        });

        test('Assigns and unassigns labels for the given range', async ({ page }) => {
            const videoRangePage = new ClassificationVideoRangesPage(page);

            await videoRangePage.createRange(0, 200, 'suit', 'ranges-item-suit-id');
            await videoRangePage.createRange(50, 150, 'value', 'ranges-item-value-id');

            await videoRangePage.createRange(300, 450, 'suit', 'ranges-item-suit-id');
            await videoRangePage.createRange(350, 400, 'No class', 'ranges-item-no-class-id');

            // Unassign label
            await videoRangePage.clickRange(1, 'ranges-item-value-id');

            await expect(videoRangePage.getRangesWithLabel('ranges-item-value-id', 'value')).toHaveCount(0);
            await expect(videoRangePage.getRangesWithLabel('ranges-item-suit-id', 'suit')).toHaveCount(5);
            await expect(videoRangePage.getRangesWithLabel('ranges-item-no-class-id', 'No class')).toHaveCount(1);
        });
    });

    test.describe('Hierarchical labels project', () => {
        test.beforeEach(setupBeforeEach(hierarchicalLabelsProject));

        test('Creates video ranges', async ({ page }) => {
            const videoRangePage = new ClassificationVideoRangesPage(page);

            // One row per group, i.e. color, red suit, black suit, value.
            await expect(videoRangePage.getRangesRow(/ranges-item/)).toHaveCount(4);

            await videoRangePage.createRange(0, 200, 'Red', 'ranges-item-color-id');
            await videoRangePage.createRange(50, 150, 'Hearts', 'ranges-item-red-suit-id');

            await videoRangePage.createRange(250, 350, 'Spades', 'ranges-item-black-suit-id');
            await videoRangePage.createRange(0, 400, 'A', 'ranges-item-values-id');

            await expect(videoRangePage.getRanges('ranges-item-color-id')).toHaveCount(7);
            await expect(videoRangePage.getRanges('ranges-item-red-suit-id')).toHaveCount(7);
            await expect(videoRangePage.getRanges('ranges-item-black-suit-id')).toHaveCount(7);
            await expect(videoRangePage.getRanges('ranges-item-values-id')).toHaveCount(7);

            await videoRangePage.createRange(100, 300, 'Clubs', 'ranges-item-black-suit-id');

            await expect(videoRangePage.getRanges('ranges-item-color-id')).toHaveCount(6);
            await expect(videoRangePage.getRanges('ranges-item-red-suit-id')).toHaveCount(6);
            await expect(videoRangePage.getRanges('ranges-item-black-suit-id')).toHaveCount(6);
            await expect(videoRangePage.getRanges('ranges-item-values-id')).toHaveCount(6);

            const createRangesPromiseRequest = page.waitForRequest((req) => {
                return req.method() === 'POST' && req.url().endsWith('range_annotation');
            });

            await videoRangePage.saveRanges();

            await expect(videoRangePage.videoRangeDialog).toBeHidden();

            const createRangesRequest = await createRangesPromiseRequest;
            const bodyJSON = createRangesRequest.postData();
            const videoRanges = bodyJSON === null ? {} : JSON.parse(bodyJSON);

            expect(videoRanges.range_labels).toEqual([
                {
                    start_frame: 0,
                    end_frame: 26,
                    label_ids: ['5bc9bb1a25b681e3ca3ff997', '5bc9bb1a25b681e3ca3ff9a4'],
                },
                {
                    start_frame: 27,
                    end_frame: 57,
                    label_ids: ['5bc9bb1a25b681e3ca3ff997', '5bc9bb1a25b681e3ca3ff998', '5bc9bb1a25b681e3ca3ff9a4'],
                },
                {
                    start_frame: 58,
                    end_frame: 183,
                    label_ids: ['5bc9bb1a25b681e3ca3ff9a4', '5bc9bb1a25b681e3ca3ff99a', '5bc9bb1a25b681e3ca3ff99c'],
                },
                {
                    start_frame: 184,
                    end_frame: 215,
                    label_ids: ['5bc9bb1a25b681e3ca3ff99a', '5bc9bb1a25b681e3ca3ff99b', '5bc9bb1a25b681e3ca3ff9a4'],
                },
                {
                    start_frame: 216,
                    end_frame: 246,
                    label_ids: ['5bc9bb1a25b681e3ca3ff9a4'],
                },
                {
                    start_frame: 247,
                    end_frame: 900,
                    label_ids: [],
                },
            ]);
        });

        test('Assigns and unassigns labels for the given range', async ({ page }) => {
            const videoRangePage = new ClassificationVideoRangesPage(page);

            await videoRangePage.createRange(0, 200, 'Red', 'ranges-item-color-id');
            await videoRangePage.createRange(50, 150, 'Hearts', 'ranges-item-red-suit-id');

            await videoRangePage.createRange(250, 350, 'Spades', 'ranges-item-black-suit-id');
            await videoRangePage.createRange(0, 400, 'A', 'ranges-item-values-id');

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await expect(videoRangePage.getLabelAssigned('Hearts')).toBeVisible();

            await videoRangePage.assignLabel('Diamonds');

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await expect(videoRangePage.getLabelAssigned('Diamonds')).toBeVisible();
            await videoRangePage.closeLabelSearch();

            await videoRangePage.openLabelSearch(1, 'ranges-item-color-id');
            await expect(videoRangePage.getLabelAssigned('Red')).toBeVisible();
            await videoRangePage.closeLabelSearch();

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await expect(videoRangePage.getLabelAssigned('Diamonds')).toBeVisible();

            await videoRangePage.unassignLabel();

            await videoRangePage.openLabelSearch(1, 'ranges-item-color-id');
            await expect(videoRangePage.getLabelAssigned('Red')).toBeVisible();
            await videoRangePage.closeLabelSearch();

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await expect(videoRangePage.getLabelAssigned('Diamonds')).toBeHidden();

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await videoRangePage.assignLabel('Hearts');

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await expect(videoRangePage.getLabelAssigned('Hearts')).toBeVisible();
            await videoRangePage.closeLabelSearch();

            await videoRangePage.openLabelSearch(1, 'ranges-item-color-id');
            await videoRangePage.unassignLabel();

            await videoRangePage.openLabelSearch(1, 'ranges-item-color-id');
            await expect(videoRangePage.getLabelAssigned('Red')).toBeHidden();
            await videoRangePage.closeLabelSearch();

            await videoRangePage.openLabelSearch(1, 'ranges-item-red-suit-id');
            await expect(videoRangePage.getLabelAssigned('Hearts')).toBeHidden();

            await expect(videoRangePage.getRangesWithLabel('ranges-item-color-id', 'Red')).toHaveCount(2);
            await expect(videoRangePage.getRangesWithLabel('ranges-item-red-suit-id', 'Hearts')).toHaveCount(0);
            await expect(videoRangePage.getRangesWithLabel('ranges-item-red-suit-id', 'Diamonds')).toHaveCount(0);
            await expect(videoRangePage.getRangesWithLabel('ranges-item-black-suit-id', 'Spades')).toHaveCount(1);
            await expect(videoRangePage.getRangesWithLabel('ranges-item-values-id', 'A')).toHaveCount(6);
        });
    });
});
