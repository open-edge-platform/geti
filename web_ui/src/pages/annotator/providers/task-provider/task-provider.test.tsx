// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { act, renderHook } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import {
    getMockedProject,
    mockedProjectContextProps,
} from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { TaskProvider, useTask } from './task-provider.component';

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(),
}));

const wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <MemoryRouter>
            <TaskProvider>{children}</TaskProvider>
        </MemoryRouter>
    );
};

describe('useTask', () => {
    it('sets default label', () => {
        const detectionLabels = [getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'detection-1' })];
        const tasks = [
            getMockedTask({
                domain: DOMAIN.DETECTION,
                labels: detectionLabels,
                title: 'classification',
                id: 'classificaiotn',
            }),
        ];

        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ project: getMockedProject({ tasks }) }));

        const { result } = renderHook(() => useTask(), { wrapper });
        expect(result.current.defaultLabel).toEqual(detectionLabels[0]);
    });

    it('does not set the default label if there are multiple local labels', () => {
        const detectionLabels = [
            getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'detection-1' }),
            getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'detection-2' }),
        ];
        const tasks = [
            getMockedTask({
                domain: DOMAIN.DETECTION,
                labels: detectionLabels,
                title: 'detection',
                id: 'detection',
            }),
        ];

        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ project: getMockedProject({ tasks }) }));

        const { result } = renderHook(() => useTask(), { wrapper });
        expect(result.current.defaultLabel).toEqual(null);
    });

    it('sets the default label for detection -> classification projects', () => {
        const detectionLabels = [getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'detection-1' })];
        const classificationLabels = [
            getMockedLabel({ behaviour: LABEL_BEHAVIOUR.GLOBAL, id: 'classification-1', parentLabelId: 'detection-1' }),
            getMockedLabel({ behaviour: LABEL_BEHAVIOUR.GLOBAL, id: 'classification-2', parentLabelId: 'detection-1' }),
        ];
        const tasks = [
            getMockedTask({ domain: DOMAIN.DETECTION, labels: detectionLabels, id: 'detection', title: 'detection' }),
            getMockedTask({
                domain: DOMAIN.CLASSIFICATION,
                labels: classificationLabels,
                id: 'classification',
                title: 'classification',
            }),
        ];

        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ project: getMockedProject({ tasks }) }));

        const { result } = renderHook(() => useTask(), { wrapper });
        expect(result.current.defaultLabel).toEqual(detectionLabels[0]);

        act(() => {
            result.current.setSelectedTask(tasks[0]);
        });
        expect(result.current.defaultLabel).toEqual(detectionLabels[0]);

        act(() => {
            result.current.setSelectedTask(tasks[1]);
        });
        expect(result.current.defaultLabel).toEqual(null);
    });

    it('sets the default label for detection -> segmentation projects', () => {
        const detectionLabels = [getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'detection-1' })];
        const segmentationLabels = [
            getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'classification-1', parentLabelId: 'detection-1' }),
            getMockedLabel({ behaviour: LABEL_BEHAVIOUR.LOCAL, id: 'classification-2', parentLabelId: 'detection-1' }),
        ];
        const tasks = [
            getMockedTask({ domain: DOMAIN.DETECTION, labels: detectionLabels, id: 'detection', title: 'detection' }),
            getMockedTask({
                domain: DOMAIN.SEGMENTATION,
                labels: segmentationLabels,
                id: 'segmentation',
                title: 'segmentation',
            }),
        ];

        jest.mocked(useProject).mockReturnValue(mockedProjectContextProps({ project: getMockedProject({ tasks }) }));

        const { result } = renderHook(() => useTask(), { wrapper });
        expect(result.current.defaultLabel).toEqual(null);

        act(() => {
            result.current.setSelectedTask(tasks[0]);
        });
        expect(result.current.defaultLabel).toEqual(detectionLabels[0]);

        act(() => {
            result.current.setSelectedTask(tasks[1]);
        });
        expect(result.current.defaultLabel).toEqual(null);
    });
});
