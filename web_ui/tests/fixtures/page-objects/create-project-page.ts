// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { ProjectPage } from './project-page';

export class CreateProjectPage {
    constructor(private page: Page) {}

    private async enterProjectName(name: string) {
        await this.page.getByRole('textbox', { name: /project name/i }).fill(name);
    }

    private async selectProjectType(
        tab: 'Detection' | 'Keypoint Detection' | 'Segmentation' | 'Classification' | 'Anomaly' | 'Chained tasks',
        domain: string
    ) {
        await this.page.getByRole('tab', { name: tab, exact: true }).click();
        await this.page.getByRole('heading', { name: new RegExp(domain, 'i') }).click();
    }

    private async nextStep() {
        await this.page.getByRole('button', { name: /next/i }).click();
    }

    private async fillLabel(name: string) {
        await this.page.getByRole('textbox', { name: /project label name input/i }).fill(name);
    }

    private async getTreeListItem(name: string, index = 0) {
        return this.page.getByRole('listitem', { name: `label item ${name}` }).nth(index);
    }

    async addGroup(name: string) {
        const groupNameTextBox = this.page.getByRole('textbox', { name: 'Label group name' }).nth(0);
        await groupNameTextBox.click();
        await groupNameTextBox.fill(name);
        await this.page.getByRole('button', { name: 'Create group' }).click();
    }

    async addChildLabel(groupName: string, labelName?: string) {
        const addChildButton = this.page
            .getByLabel(`${groupName} group`)
            .getByRole('button', { name: 'add child label button' });
        await addChildButton.click();
        labelName && (await this.changeLabelName('Label', labelName));
    }

    async addChildGroup(labelName: string, groupName: string) {
        const defaultGroupName = 'Group';
        const addChildButton = this.page
            .getByLabel(`${labelName} label`)
            .nth(0)
            .getByRole('button', { name: 'add child group button' });

        await addChildButton.click();
        await this.changeGroupName(defaultGroupName, groupName);
    }

    async addLabel(name: string) {
        await this.fillLabel(name);
        await this.page.getByRole('button', { name: /create label/i }).click();
    }

    async changeGroupName(oldName: string, newName: string) {
        await this.page.getByTestId(`${oldName}-project-label-group-input-id`).fill(newName);
    }

    async changeLabelName(oldName: string, newName: string) {
        await this.page.locator(`#label-tree-${oldName}-${oldName}`).fill(newName);
    }

    async createLabelHierarchy(labels: Record<string, string[]>) {
        for (const group of Object.keys(labels)) {
            await this.page
                .getByRole('textbox', { name: /Label group name/i })
                .nth(0)
                .fill(group);
            await this.page.getByRole('button', { name: /create group/i }).click();

            const groupList = this.page.getByRole('listitem', { name: `label item ${group}` });
            const groupListItem = groupList.getByLabel(`${group} group`);

            const editBoxes = groupList.getByRole('textbox', { name: /edited name/i });

            for (let labelIdx = 0; labelIdx < labels[group].length; labelIdx++) {
                const label = labels[group][labelIdx];

                await groupListItem.hover();
                const currentLabel = editBoxes.nth(labelIdx);
                if (!(await currentLabel.isVisible())) {
                    await groupList.getByRole('button', { name: 'add child label button' }).click();
                }

                await editBoxes.nth(0).fill(label);
            }
        }
    }

    private async create() {
        await this.page.getByRole('button', { name: 'Create', exact: true }).click();
        return new ProjectPage(this.page);
    }

    async selectClassificationSingleLabelAndGoToLabels(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Classification', 'single label');
        await this.nextStep();
    }

    async selectClassificationHierarchicalAndGoToLabels(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Classification', 'hierarchical');
        await this.nextStep();
    }

    async classification(name: string, labels: string[]) {
        await this.selectClassificationSingleLabelAndGoToLabels(name);

        for (const label of labels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async classificationMultiLabel(name: string, labels: string[]) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Classification', 'multi label');
        await this.nextStep();

        for (const label of labels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async classificationHierarchical(name: string, labels: Record<string, string[]>) {
        await this.selectClassificationHierarchicalAndGoToLabels(name);

        // Classification task
        await this.createLabelHierarchy(labels);

        return await this.create();
    }

    async detection(name: string, labels: string[]) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Detection', 'Detection bounding box');
        await this.nextStep();

        for (const label of labels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async keypointDetection(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();

        await this.page.getByRole('tab', { name: /Keypoint Detection/i }).click();
        await this.nextStep();

        await this.page.getByLabel('drawing box').click({ position: { x: 100, y: 100 } });
        await this.page.getByLabel('drawing box').click({ position: { x: 200, y: 100 } });

        return await this.create();
    }

    async keypointDetectionTemplate(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.page.getByRole('tab', { name: /Keypoint Detection/i }).click();

        return await this.nextStep();
    }

    async orientedDetection(name: string, labels: string[]) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Detection', 'Detection oriented');
        await this.nextStep();

        for (const label of labels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async segmentation(name: string, labels: string[]) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Segmentation', 'Semantic segmentation');
        await this.nextStep();

        for (const label of labels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async instanceSegmentation(name: string, labels: string[]) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.selectProjectType('Segmentation', 'Instance segmentation');
        await this.nextStep();

        for (const label of labels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async detectionClassification(
        name: string,
        detectionLabel: string,
        classificationLabels: Record<string, string[]>
    ) {
        await this.enterProjectName(name);
        await this.nextStep();

        await this.page.getByRole('tab', { name: /chained tasks/i }).click();
        await this.page.getByRole('heading', { name: /classification/i }).click();

        await this.nextStep();

        // Detection task
        await this.fillLabel(detectionLabel);
        await this.nextStep();

        // Classification task
        await this.createLabelHierarchy(classificationLabels);

        return await this.create();
    }

    async detectionSegmentation(name: string, detectionLabel: string, segmentationLabels: string[]) {
        await this.enterProjectName(name);
        await this.nextStep();

        await this.page.getByRole('tab', { name: /chained tasks/i }).click();
        await this.page.getByRole('heading', { name: /segmentation/i }).click();

        await this.nextStep();

        // Detection task
        await this.fillLabel(detectionLabel);
        await this.nextStep();

        // Segmentation task
        for (const label of segmentationLabels) {
            await this.addLabel(label);
        }

        return await this.create();
    }

    async anomalyClassification(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();

        await this.page.getByRole('tab', { name: /anomaly/i }).click();
        await this.page.getByRole('heading', { name: /anomaly classification/i }).click();

        return await this.create();
    }

    async anomalyDetection(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();
        await this.page.getByRole('tab', { name: /anomaly/i }).click();
        await this.page.getByRole('heading', { name: /anomaly detection/i }).click();

        return await this.create();
    }

    async anomalySegmentation(name: string) {
        await this.enterProjectName(name);
        await this.nextStep();

        await this.page.getByRole('tab', { name: /anomaly/i }).click();
        await this.page.getByRole('heading', { name: /anomaly segmentation/i }).click();

        return await this.create();
    }

    async changeColorInEdition(color: string) {
        const colorInput = this.page.getByTestId('popover').getByRole('textbox');
        await colorInput.click();
        await colorInput.fill(color);
        await colorInput.press('Enter');

        const confirmButton = this.page.getByRole('button', { name: 'Confirm' });
        await confirmButton.click();
    }

    async checkColor(labelName: string, labelId: string, rgbColor: string) {
        const colorRectangle = this.page.locator(`#label-tree-${labelName}-${labelId}-color-selected-color`);
        const background = await colorRectangle.getAttribute('style');
        expect(background).toMatch(`background-color: ${rgbColor}`);
    }

    async getLabelsValidationErrors() {
        return this.page.getByTestId('label-error-message-id');
    }

    async getLabelError(name: string, index = 0) {
        const label = await this.getTreeListItem(name, index);
        return label.getByTestId('label-error-message-id');
    }

    async removeItem(name: string, type: 'label' | 'group', index = 0) {
        const removalButton = this.page
            .getByLabel(`${name} ${type}`)
            .nth(index)
            .getByTestId(/delete-label-button/);

        await removalButton.click();
    }
}
