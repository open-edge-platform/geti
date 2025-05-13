// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { ShapeType } from '../../../../../../core/annotations/shapetype.enum';
import { getMockedAnnotation } from '../../../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getMockedLabel, getMockedLabels } from '../../../../../../test-utils/mocked-items-factory/mocked-labels';
import { mockedProjectContextProps } from '../../../../../../test-utils/mocked-items-factory/mocked-project';
import { ToolType } from '../../../../core/annotation-tool-context.interface';
import { renderApp } from './renders';

jest.mock('../../../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => mockedProjectContextProps({})),
}));

jest.mock('../../../../providers/annotation-scene-provider/annotation-scene-provider.component', () => ({
    ...jest.requireActual('../../../../providers/annotation-scene-provider/annotation-scene-provider.component'),
    useAnnotationScene: jest.fn(() => ({ isDrawing: false, annotations: [] })),
}));

describe('Label shortcuts', () => {
    const labels3 = getMockedLabels(3);

    beforeEach(() => {
        jest.restoreAllMocks();

        Element.prototype.scrollIntoView = jest.fn();
    });

    afterAll(() => {
        jest.clearAllTimers();
    });

    it('does not update grabcut settings if "isDrawing" is false', async () => {
        const addLabelMock = jest.fn();
        const updateToolSettingsMock = jest.fn();

        await renderApp({
            annotations: [],
            labels: labels3,
            addLabel: addLabelMock,
            removeLabels: jest.fn(),
            tool: ToolType.GrabcutTool,
            updateToolSettings: updateToolSettingsMock,
        });

        await userEvent.click(screen.getByRole('button', { name: labels3[0].name }));
        expect(updateToolSettingsMock).not.toBeCalled();
    });

    it('updates grab-cut settings when label is local', async () => {
        const annotations = [
            getMockedAnnotation(
                {
                    id: '1',
                    isSelected: true,
                    labels: [{ ...labels3[0], source: { userId: '123321' } }],
                },
                ShapeType.Polygon
            ),
        ];

        const updateToolSettingsMock = jest.fn();
        const localLabel = getMockedLabel({ isExclusive: true });

        await renderApp({
            annotations,
            labels: [localLabel],
            tool: ToolType.GrabcutTool,
            updateToolSettings: updateToolSettingsMock,
            isDrawing: true,
        });

        await userEvent.click(screen.getByRole('button', { name: localLabel.name }));
        expect(updateToolSettingsMock).toHaveBeenCalledWith(ToolType.GrabcutTool, {
            selectedLabel: localLabel,
        });
    });
});
