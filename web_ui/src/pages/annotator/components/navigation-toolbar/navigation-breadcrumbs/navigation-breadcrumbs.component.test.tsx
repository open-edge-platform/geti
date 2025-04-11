// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { useSubmitAnnotations } from '../../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { NavigationBreadcrumbs } from './navigation-breadcrumbs.component';

jest.mock('../../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        labels: [],
        tasks: [],
    })),
}));

jest.mock('../../../providers/submit-annotations-provider/submit-annotations-provider.component', () => ({
    ...jest.requireActual('../../../providers/submit-annotations-provider/submit-annotations-provider.component'),
    useSubmitAnnotations: jest.fn(() => ({
        confirmSaveAnnotations: async (callback: () => Promise<void>) => await callback(),
    })),
}));

jest.mock('../../../hooks/use-annotator-scene-interaction-state.hook', () => ({
    useIsSceneBusy: jest.fn(() => false),
}));

const mockedSetExplanationVisible = jest.fn();
jest.mock('../../../providers/prediction-provider/prediction-provider.component', () => ({
    usePrediction: jest.fn(() => ({ setExplanationVisible: mockedSetExplanationVisible })),
}));

jest.mock('../../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(() => ({
        toggleToolOnTaskChange: jest.fn(),
    })),
}));

describe('NavigationBreadcrumbs', () => {
    const breadcrumbItems = ['All Tasks', DOMAIN.SEGMENTATION, DOMAIN.CLASSIFICATION];

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it.each(breadcrumbItems)('renders the correct breadcrumb items', async (item) => {
        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: [
                { id: '20', domain: DOMAIN.SEGMENTATION },
                { id: '30', domain: DOMAIN.CLASSIFICATION },
            ],
        }));

        render(<NavigationBreadcrumbs />);

        await waitFor(() => {
            expect(screen.queryByText(item)).toBeTruthy();
        });
    });

    it('selects "All tasks" by default', async () => {
        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: [
                { id: '20', domain: DOMAIN.SEGMENTATION },
                { id: '30', domain: DOMAIN.CLASSIFICATION },
            ],
        }));

        render(<NavigationBreadcrumbs />);

        await waitFor(() => {
            expect(screen.queryByText('All Tasks')).toBeTruthy();
        });

        expect(screen.queryByText('All Tasks')).toHaveClass('selected');
    });

    it('switches task correctly', async () => {
        const mockSetSelectedTask = jest.fn();

        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: [
                { id: '20', domain: DOMAIN.SEGMENTATION },
                { id: '30', domain: DOMAIN.CLASSIFICATION },
            ],
            setSelectedTask: mockSetSelectedTask,
        }));

        render(<NavigationBreadcrumbs />);

        act(() => {
            fireEvent.click(screen.getByText(DOMAIN.SEGMENTATION));
        });

        expect(mockSetSelectedTask).toHaveBeenCalled();
    });

    it('selecting all-task set ExplanationVisible to false', async () => {
        const mockSetSelectedTask = jest.fn();

        (useTask as jest.Mock).mockImplementation(() => ({
            tasks: [
                { id: '20', domain: DOMAIN.SEGMENTATION },
                { id: '30', domain: DOMAIN.CLASSIFICATION },
            ],
            setSelectedTask: mockSetSelectedTask,
        }));

        render(<NavigationBreadcrumbs />);

        act(() => {
            fireEvent.click(screen.getByText('All Tasks'));
        });

        expect(mockedSetExplanationVisible).toHaveBeenCalledWith(false);
    });

    it("doesn't ask for confirmation when switching to the same task", async () => {
        const confirmSaveAnnotations = jest.fn();

        // @ts-expect-error We don't care about mocking other values
        jest.mocked(useSubmitAnnotations).mockImplementation(() => ({
            confirmSaveAnnotations,
        }));

        const mockSetSelectedTask = jest.fn();

        const tasks = [
            { id: '20', domain: DOMAIN.SEGMENTATION },
            { id: '30', domain: DOMAIN.CLASSIFICATION },
        ];
        const selectedTask = tasks[0];

        // @ts-expect-error We don't care about mocking other values
        jest.mocked(useTask).mockImplementation(() => ({
            tasks,
            setSelectedTask: mockSetSelectedTask,
            selectedTask,
        }));

        render(<NavigationBreadcrumbs />);

        act(() => {
            fireEvent.click(screen.getByText(selectedTask.domain));
        });

        expect(confirmSaveAnnotations).not.toHaveBeenCalled();
        expect(mockSetSelectedTask).not.toHaveBeenCalled();
    });
});
