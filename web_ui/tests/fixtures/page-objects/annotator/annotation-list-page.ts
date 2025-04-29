// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Locator, Page } from '@playwright/test';

import { clickAndMove } from '../../../utils/mouse';
import { expect } from './../../base-test';

export class AnnotationListPage {
    constructor(private page: Page) {}

    async getTotalAnnotations() {
        const text = await this.getSelectAllAriaLabel();
        const matchImages = text.match(/out of (\d+) annotations selected/);

        if (matchImages) {
            return Number(matchImages[1]);
        }

        return 0;
    }

    async expectTotalAnnotationsToBe(n: number) {
        const checkbox = this.page.getByRole('checkbox', { name: /\d+ out of \d+ annotations selected/ });
        await expect(checkbox).toBeVisible();

        await expect(checkbox).toHaveAttribute('aria-label', new RegExp(`out of ${n} annotations selected`));
    }

    async getTotalSelectedAnnotations() {
        const text = await this.getSelectAllAriaLabel();
        const matchImages = text.match(/(\d+) out of/);

        if (matchImages) {
            return Number(matchImages[1]);
        }

        return 0;
    }

    private async getSelectAllAriaLabel(): Promise<string> {
        const checkbox = this.page.getByRole('checkbox', { name: /\d+ out of \d+ annotations selected/ });
        await expect(checkbox).toBeVisible();

        return (await checkbox.getAttribute('aria-label')) ?? '';
    }

    async selectAll() {
        await this.page
            .getByRole('checkbox', {
                name: new RegExp(`\\d+ out of \\d+ annotations selected`),
            })
            .check();
    }

    async deselectAll() {
        await this.page
            .getByRole('checkbox', {
                name: new RegExp(`\\d+ out of \\d+ annotations selected`),
            })
            .uncheck();
    }

    async lockSelected() {
        await this.page.getByRole('button', { name: 'lock annotation' }).click();
    }

    async hideSelected() {
        await this.page.getByTestId('annotation-selected-annotations-toggle-visibility').click();
    }

    async removeSelected() {
        await this.page.getByRole('button', { name: 'Delete selected annotations' }).click();
    }

    async assignLabelsOfSelected() {
        await this.page.getByRole('button', { name: 'Assign label to selected annotations' }).click();
    }

    async getAnnotationListItem(listItem: Locator): Promise<AnnotationListItemPage> {
        return new AnnotationListItemPage(this.page, listItem);
    }

    async moveThresholdSliderUp(newValue: number) {
        await this.page.getByRole('button', { name: /filter-by-score-button/i }).click();

        const slider = this.page.getByRole('slider', { name: /filter-by-score-slider/i });
        const container = this.page.getByRole('group', { name: /filter-by-score-slider/i });
        const { width: containerWidth } = (await container.boundingBox()) ?? { width: 0 };

        const nextStep = containerWidth / 11;
        let sliderVale = await slider.inputValue();

        while (sliderVale !== '1' && Number(sliderVale) < newValue / 100) {
            const sensitivitySliderBoundingBox = await slider.boundingBox();

            if (!sensitivitySliderBoundingBox) {
                throw new Error('Bounding box not found');
            }

            const { x, y, width, height } = sensitivitySliderBoundingBox;

            const startPoint = { x: x + width / 2, y: y + height / 2 };
            const endPosition = { x: (startPoint.x += nextStep), y: startPoint.y };

            await clickAndMove(this.page, startPoint, endPosition);
            sliderVale = await slider.inputValue();
        }

        // Close the slider dialog
        await this.page.mouse.click(0, 0);

        return sliderVale;
    }

    async getVisibleAnnotations() {
        return this.page
            .getByLabel('Annotations list')
            .getByLabel(/Annotation with id/)
            .all();
    }
}

class AnnotationListItemPage {
    constructor(
        private page: Page,
        private listItem: Locator
    ) {}

    async hover() {
        await this.listItem.hover();
    }

    async select() {
        await this.listItem.getByRole('checkbox').check();
    }

    async deselect() {
        await this.listItem.getByRole('checkbox').uncheck();
    }

    async showActions(callback: (menu: Locator) => Promise<void>) {
        await this.hover();
        await this.listItem.getByRole('button', { name: /show actions/i }).click();

        const menu = this.page.getByRole('menu');
        await expect(menu).toBeVisible();
        await callback(menu);
        await expect(menu).toBeHidden();
    }

    async unlock() {
        await this.listItem.getByRole('button', { name: /unlock/i }).click();
    }

    async show() {
        await this.listItem.getByRole('button', { name: 'Show', exact: true }).click();
    }

    async annotationIsVisible(): Promise<boolean> {
        return this.listItem.getByRole('button', { name: 'Show', exact: true }).isVisible();
    }

    async isLocked(): Promise<boolean> {
        return this.listItem.getByRole('button', { name: /unlock/i }).isVisible();
    }

    async labels(): Promise<string[]> {
        const labels = this.listItem
            .getByLabel(/Labels of/)
            .getByRole('listitem')
            .all();

        return await Promise.all(
            (await labels).map(async (label): Promise<string> => (await label.allInnerTexts()).join(''))
        );
    }
}
