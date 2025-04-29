// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

export interface SingleLabelApi {
    name: string;
    color: string;
    id: string;
    group: string;
    is_anomalous: boolean;
    is_empty: boolean;
    hotkey: string;
}

// Note: rest of fields are not needed
interface LabelPayload {
    name: string;
}

export class LabelsPage {
    constructor(private page: Page) {}

    async getEditLabelButtonLocator() {
        return this.page.getByRole('button', { name: 'Edit labels' });
    }

    async getCancelEditingButtonLocator() {
        return this.page.getByRole('button', { name: 'Cancel editing' });
    }

    async enableEditing() {
        const editButton = await this.getEditLabelButtonLocator();

        await editButton.click();
    }

    async cancelEditing() {
        const editButton = await this.getCancelEditingButtonLocator();

        await editButton.click();
    }

    async createLabel(name: string, color?: string, keyboardShortcut?: string) {
        const labelNameInputLocator = this.page.getByLabel('Project label name input');
        await labelNameInputLocator.fill(name);

        if (color) {
            const changeColorButtonLocator = this.page.locator('[data-testid="change-color-button"]');

            await changeColorButtonLocator.click();
            // TODO: will be implemented in case of adding color input field
        }

        if (keyboardShortcut) {
            const addKeyboardShortcutButtonLocator = this.page.locator('[data-testid="hotkey-name-field"]');

            await addKeyboardShortcutButtonLocator.click();
            await this.page.keyboard.press(keyboardShortcut);
        }

        const saveButtonLocator = this.page.getByRole('button', { name: /Create label/i });
        if (await saveButtonLocator.isEnabled()) {
            await saveButtonLocator.click();
        }
    }

    async editLabel(label?: Partial<SingleLabelApi>, newName?: string, color?: string, keyboardShortcut?: string) {
        if (newName && label?.name) {
            const labelNameInputLocator = this.page.getByTestId(`label-tree-${label?.name}-name-input`);
            await labelNameInputLocator.selectText();
            await this.page.keyboard.press('Backspace');
            await this.page.getByTestId('label-tree--name-input').fill(newName);
        }

        if (color && label?.name && label?.group) {
            const changeColorButtonLocator = this.page.getByRole('button', {
                name: `${label.name} Color picker button`,
            });

            await changeColorButtonLocator.click();

            const colorInput = this.page.getByRole('dialog').getByRole('textbox');
            await colorInput.click();
            await colorInput.fill(color);
            await colorInput.press('Enter');

            const confirmButton = this.page.getByRole('button', { name: 'Confirm' });
            await confirmButton.click();

            await expect(this.page.getByRole('dialog')).toBeHidden({ timeout: 10000 });
        }

        if (keyboardShortcut && label?.name) {
            const addKeyboardShortcutButtonLocator = this.page
                .getByLabel(`label item ${label.name}`)
                .getByLabel('edited hotkey');

            await addKeyboardShortcutButtonLocator.focus();
            await this.page.keyboard.press(keyboardShortcut);
        }
    }

    async deleteLabel(label: SingleLabelApi) {
        const deleteButtonLocator = this.page.getByTestId(`${label.name}-label-delete-label-button`);

        await deleteButtonLocator.click();
    }

    async deleteGroup(groupName: string) {
        const deleteButtonLocator = this.page.getByTestId(`${groupName}-group-delete-label-button`);

        await deleteButtonLocator.click();
    }

    async createGroup(name: string) {
        const groupNameInputLocator = this.page.getByLabel('Label group name');
        await groupNameInputLocator.fill(name);

        const saveButtonLocator = this.page.getByRole('button', { name: /Create group/i });

        if (await saveButtonLocator.isEnabled()) {
            await saveButtonLocator.click();
        }
    }

    async editGroup(newName?: string) {
        if (newName) {
            await this.page.keyboard.press('Backspace');

            // The first one will be the top input (new group independent from all other labels)
            // So the second will be the current one we're editing
            const groupNameInputLocator = this.page.getByTestId(`empty-project-label-group-input-id`);

            await groupNameInputLocator.fill(newName);
        }
    }

    async createLabelInGroup(groupName: string, label?: SingleLabelApi, color?: string, keyboardShortcut?: string) {
        const addLabelButtonLocator = this.page
            .getByLabel(`label item ${groupName}`)
            .getByRole('button', { name: 'add child label button' });
        await addLabelButtonLocator.click();

        await this.editLabel({ name: 'Label' }, label?.name, color, keyboardShortcut);
    }

    async createGroupInLabel(label: SingleLabelApi, groupName: string) {
        const addGroupButtonLocator = this.page.getByTestId(
            `${label.name.toLocaleLowerCase()}-label-add-child-group-button`
        );

        await addGroupButtonLocator.click();
        await this.editGroup(groupName);
    }

    async getTaskLabelsTree(domain: string) {
        return this.page.locator(`#labels-management-${domain}-id`);
    }

    async getAllItemsFromTask(domain: string) {
        return (await this.getTaskLabelsTree(domain)).locator('li');
    }

    async getNthItemFromTask(domain: string, n: number) {
        return (await this.getTaskLabelsTree(domain)).locator('li').nth(n);
    }

    async changeNameOfNthItem(taskType: string, n: number, newName: string) {
        await (await this.getNthItemFromTask(taskType, n)).getByRole('textbox', { name: 'edited name' }).fill(newName);
    }

    async getSavingLabelsRequest(projectId: string, savingButtonName: string) {
        const [savingRequest] = await Promise.all([
            this.page.waitForRequest((request) => {
                return request.url().endsWith(`/projects/${projectId}`) && request.method() === 'PUT';
            }),
            this.page.getByRole('button', { name: savingButtonName }).click(),
        ]);

        return savingRequest;
    }

    async getLabelsFromPayloadByName(labels: LabelPayload[], name: string) {
        return labels.find((label: LabelPayload) => label.name === name);
    }

    async saveLabels() {
        await this.page.getByRole('button', { name: /Save/i }).click();
    }

    async assignNewLabels() {
        await this.page.getByRole('button', { name: 'Assign', exact: true }).click();
    }
}
