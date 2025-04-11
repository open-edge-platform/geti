// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { screen } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import {
    getMockedProject,
    mockedProjectContextProps,
} from '../../../../test-utils/mocked-items-factory/mocked-project';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ActionButton } from '../../button/button.component';
import { MediaItemAnnotationsPreviewDialog } from './media-item-annotations-preview-dialog.component';

jest.mock('../../../../pages/annotator/zoom/zoom-provider.component', () => ({
    useZoom: jest.fn(() => ({ zoomState: { zoom: 1.0, translation: { x: 0, y: 0 } } })),
}));

jest.mock('../../../../pages/project-details/providers/project-provider/project-provider.component', () => ({
    ...jest.requireActual('../../../../pages/project-details/providers/project-provider/project-provider.component'),
    useProject: jest.fn(() => ({
        project: { tasks: [] },
    })),
}));

jest.mock('react-zoom-pan-pinch', () => ({
    ...jest.requireActual('react-zoom-pan-pinch'),
    useControls: jest.fn(() => ({
        resetTransform: jest.fn(),
    })),
}));

describe('MediaItemAnnotationsPreviewDialogComponent', () => {
    const close = jest.fn();

    beforeEach(() => {
        jest.mocked(useProject).mockImplementation(() =>
            mockedProjectContextProps({
                project: getMockedProject({
                    tasks: [
                        {
                            id: 'task-id',
                            domain: DOMAIN.DETECTION,
                            title: 'Detection',
                            labels: [getMockedLabel({ name: 'cat' })],
                        },
                    ],
                }),
            })
        );
    });

    it('Check if dialog has default button and passed content', async () => {
        render(
            <MediaItemAnnotationsPreviewDialog
                close={close}
                title={'Test title'}
                subTitle={'test subtitle'}
                datasetPreview={<></>}
            >
                <span>Content of the dialog</span>
            </MediaItemAnnotationsPreviewDialog>
        );

        expect(screen.getByText('Content of the dialog')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'close preview modal' })).toBeInTheDocument();
        expect(screen.getByText('Test title')).toBeInTheDocument();
        expect(screen.getByText('test subtitle')).toBeInTheDocument();
    });

    it('Check if additional buttons are displayed properly', async () => {
        render(
            <MediaItemAnnotationsPreviewDialog
                close={close}
                additionalButtons={[<ActionButton key={'test'}>Test</ActionButton>]}
                title={'Test title'}
                subTitle={'test subtitle'}
                datasetPreview={<></>}
            >
                <span>content</span>
            </MediaItemAnnotationsPreviewDialog>
        );

        expect(screen.getByRole('button', { name: 'Test' })).toBeInTheDocument();
    });
});
