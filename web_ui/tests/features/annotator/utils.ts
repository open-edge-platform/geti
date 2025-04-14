// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator, Page } from '@playwright/test';

import { SHAPE_TYPE_DTO, ShapeDTO } from '../../../src/core/annotations/dtos/annotation.interface';
import { Point, Rect } from '../../../src/core/annotations/shapes.interface';
import { ShapeType } from '../../../src/core/annotations/shapetype.enum';
import { transformToClipperShape } from '../../../src/pages/annotator/tools/utils';
import { clickAndMove, withRelative } from '../../utils/mouse';

export const selectShape = async (page: Page, shape: ShapeDTO) => {
    const relative = await withRelative(page);

    // Select the shape by clicking on the center of the shape
    if (shape.type === SHAPE_TYPE_DTO.RECTANGLE) {
        const position = relative(shape.x + shape.width / 2, shape.y + shape.height / 2);
        await page.mouse.click(position.x, position.y);
    }
};

export const translateShape = async (page: Page, shape: ShapeDTO, newPosition: { x: number; y: number }) => {
    const relative = await withRelative(page);

    if (shape.type === SHAPE_TYPE_DTO.RECTANGLE) {
        const target = relative(newPosition.x + shape.width / 2, newPosition.y + shape.height / 2);
        const source = relative(shape.x + shape.width / 2, shape.y + shape.height / 2);
        await clickAndMove(page, source, target);
    }
};

export const getCanvasCoordinates = async (page: Page): Promise<Omit<Rect, 'shapeType'>> => {
    const canvas = page.locator('svg[role=editor] > rect');
    const [x, y, width, height] = await Promise.all([
        canvas.getAttribute('x'),
        canvas.getAttribute('y'),
        canvas.getAttribute('width'),
        canvas.getAttribute('height'),
    ]);

    return { x: Number(x), y: Number(y), width: Number(width), height: Number(height) };
};

export const getPolylinePoints = async (polyline: Locator): Promise<Point[]> => {
    const polylineHTMLPoints = await polyline.getAttribute('points');

    const polylinePoints: Point[] =
        polylineHTMLPoints?.split(' ').map((point) => {
            const [x, y] = point.split(',');

            return { x: Number(x), y: Number(y) };
        }) || [];

    return polylinePoints;
};
export const getPolylineArea = async (polyline: Locator): Promise<number> => {
    const polylinePoints = await getPolylinePoints(polyline);

    const polylineClipperShape = transformToClipperShape({ points: polylinePoints, shapeType: ShapeType.Polygon });

    return Math.abs(polylineClipperShape.totalArea());
};

export const getAnnotationsCount = async (page: Page) => {
    const annotationsList = page.getByLabel('Annotations list').getByRole('listitem', { name: /Annotation with id/ });

    return await annotationsList.count();
};

export const getLine = (x: number, y: number, length: number) => {
    return {
        points: [
            { x, y },
            { x: x + length, y },
        ],
    };
};

export const toggleShowPredictions = async (page: Page, newChecked: boolean) => {
    await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();
    await page.getByRole('button', { name: 'Settings' }).click();
    await page.getByRole('tab', { name: 'Active learning' }).click();

    const inputSwitch = page.getByRole('switch', { name: 'Show Predictions' });
    const isChecked = await inputSwitch.isChecked();

    if ((newChecked && !isChecked) || (!newChecked && isChecked)) {
        await inputSwitch.click();
        await page.getByRole('button', { name: 'Save settings' }).click();
    } else {
        await page.getByRole('button', { name: 'Cancel' }).click();
    }
};

// More details: https://github.com/microsoft/playwright/issues/13855#issuecomment-1144645091
export const dragAndDrop = async (page: Page, subjectSelector: string, targetSelector: string) => {
    const subjectElement = await page.waitForSelector(subjectSelector);
    const targetElement = await page.waitForSelector(targetSelector);

    const subjectElementBound = (await subjectElement.boundingBox()) as DOMRect;
    const targetElementBound = (await targetElement.boundingBox()) as DOMRect;

    await page.mouse.move(
        subjectElementBound.x,
        subjectElementBound.y,
        { steps: 10 } // this is the most important part!
    );

    await page.dispatchEvent(subjectSelector, 'mousedown', {
        button: 0,
        force: true,
    });

    // the x and y below is up to you to determine, in my case it was a checkers game so I needed to calculate a bit
    // if you are using with lists, you might try and consider the numbers below..

    const x = targetElementBound.x + targetElementBound.width / 2;
    const y = targetElementBound.y + targetElementBound.height / 2;

    // steps are needed here as well
    await page.mouse.move(x, y, { steps: 10 });

    await page.dispatchEvent(targetSelector, 'mouseup', {
        button: 0,
    });
};

export type RangesRowType = string | RegExp;

export class VideoRangePage {
    public defaultRow: RangesRowType;

    constructor(
        protected page: Page,
        protected rowId?: RangesRowType
    ) {
        this.defaultRow = rowId || 'ranges-item-anomaly-labels-id';
    }

    async openVideoRangeDialog() {
        await this.page.getByRole('menuitem', { name: 'Quick annotation' }).click();
    }

    get videoRangeDialog() {
        return this.page.getByRole('dialog');
    }

    getVideoRangeDialogHeader() {
        return this.page.getByRole('heading', { name: 'Quick annotation - label ranges' });
    }

    async saveRanges() {
        await this.page.getByRole('button', { name: 'Save ranges' }).click();
    }

    get videoTimelineSlider() {
        return this.page.getByTestId('video-timeline-slider-id');
    }

    get videoThumb() {
        return this.page.getByLabel('Video thumb');
    }

    async getVideoThumbBox() {
        const box = await this.videoThumb.boundingBox();
        return box as DOMRect;
    }

    get startRangeThumb() {
        return this.page.getByLabel('Start range');
    }

    async getStartRangeThumbBox() {
        const box = await this.startRangeThumb.boundingBox();
        return box as DOMRect;
    }

    get endRangeThumb() {
        return this.page.getByLabel('End range');
    }
    async getEndRangeThumbBox() {
        const box = await this.endRangeThumb.boundingBox();
        return box as DOMRect;
    }

    async moveVideoSliderThumb(start: number) {
        const videoSlider = this.videoTimelineSlider;
        const videoSliderBox = (await videoSlider.boundingBox()) as DOMRect;
        const videoThumbBox = await this.getVideoThumbBox();

        const videoSliderStartX = videoSliderBox.x - videoThumbBox.width;
        const videoThumbStartX = videoThumbBox.x;
        const end = videoSliderStartX + start;

        await clickAndMove(this.page, { x: videoThumbStartX, y: videoThumbBox.y }, { x: end, y: videoThumbBox.y });
    }

    async selectRange(start: number, end: number) {
        await this.moveVideoSliderThumb(start);

        const endRangeBox = await this.getEndRangeThumbBox();
        const videoSliderBox = (await this.videoTimelineSlider.boundingBox()) as DOMRect;

        const offset = endRangeBox.width / 2;
        const endRangeXNotOverlappedByVideoThumb = endRangeBox.x + offset;
        const endRangeX = videoSliderBox.x + end;

        await clickAndMove(
            this.page,
            { x: endRangeXNotOverlappedByVideoThumb, y: endRangeBox.y },
            { x: endRangeX, y: endRangeBox.y }
        );
    }

    getAddRangeArea(row: RangesRowType = this.defaultRow) {
        return this.getRangesRow(row).getByLabel('Add range');
    }

    getLabel(label: string) {
        return this.getLabelSearchResults().getByLabel(`label item ${label}`);
    }

    async assignLabelToNewRange(label: string, row: RangesRowType = this.defaultRow) {
        await this.getAddRangeArea(row).click();

        const labelSearchResults = await this.getLabelSearchResults().count();
        if (labelSearchResults > 0) {
            await this.getLabel(label).click();
        }
    }

    async createRange(start: number, end: number, label: string, row: RangesRowType = this.defaultRow) {
        await this.selectRange(start, end);
        await this.assignLabelToNewRange(label, row);
    }

    getRanges(row: RangesRowType = this.defaultRow) {
        return this.getRangesRow(row).getByLabel(/Click to change label from/);
    }

    async changeLabel(label: string, row: RangesRowType = this.defaultRow) {
        await this.getRanges(row).first().click();
        await this.getLabel(label).click();
    }

    async toggleRangeSelector() {
        return this.page.getByRole('button', { name: 'Range selector' }).click();
    }

    getRangesRow(row: RangesRowType | RegExp = this.defaultRow) {
        return this.page.getByTestId(row);
    }

    getLabelSearchResults() {
        return this.page.getByLabel('Label search results');
    }
}
