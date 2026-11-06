// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, type Page } from '@playwright/test';

import type { Point } from '../../src/shared/types';
import { withRelative } from '../utils/mouse';

export class MagneticLassoToolPage {
    constructor(private page: Page) {}

    // Going through the selection tool also discards any outline in progress.
    async selectTool() {
        await this.page.getByRole('button', { name: 'Selection' }).click();
        await this.page.getByRole('button', { name: 'Magnetic Lasso' }).click();
    }

    async click() {
        await this.page.mouse.down();
        await this.page.mouse.up();
    }

    private async getDrawnPointsCount() {
        const points = await this.page.getByLabel('new polygon').getAttribute('points', { timeout: 1_000 });

        return points?.trim().split(/\s+/).length ?? 0;
    }

    // Hovering makes the worker compute the edge-snapped segment to the cursor; it shows up on the next pointer move.
    async hoverUntilSnapped(target: Point) {
        const pointsBefore = await this.getDrawnPointsCount();

        await this.page.mouse.move(target.x, target.y, { steps: 5 });

        let nudge = 1;
        await expect(async () => {
            nudge = -nudge;
            await this.page.mouse.move(target.x + nudge, target.y);

            expect(await this.getDrawnPointsCount()).toBeGreaterThan(pointsBefore + 1);
        }).toPass({ timeout: 10_000 });

        await this.page.mouse.move(target.x, target.y);
    }

    // Places the first point of `outline` (in image coordinates) and waits until the worker snaps the segment towards
    // the second one. Returns the outline in screen coordinates.
    async startOutline(outline: Point[], { selectTool = true } = {}) {
        let points: Point[] = [];

        const attempt = async () => {
            if (selectTool) {
                await this.selectTool();
            }

            // Resolved here because the initial zoom-to-fit may still be settling on the first attempt.
            const relative = await withRelative(this.page);
            points = outline.map(({ x, y }) => relative(x, y));

            await this.page.mouse.move(points[0].x, points[0].y);
            await this.click();
            await this.hoverUntilSnapped(points[1]);
        };

        if (selectTool) {
            // The worker boots in the background; restart the outline until it responds.
            await expect(attempt).toPass({ timeout: 60_000 });
        } else {
            await attempt();
        }

        return points;
    }
}
