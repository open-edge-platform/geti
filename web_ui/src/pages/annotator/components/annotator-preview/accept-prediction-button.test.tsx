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

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { AnnotationThresholdProvider } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import {
    PredictionContextProps,
    usePrediction,
} from '../../providers/prediction-provider/prediction-provider.component';
import { AcceptPredictionButton } from './accept-prediction-button.component';

jest.mock('../../providers/annotation-tool-provider/annotation-tool-provider.component', () => ({
    ...jest.requireActual('../../providers/annotation-tool-provider/annotation-tool-provider.component'),
    useAnnotationToolContext: jest.fn(),
}));

jest.mock('../../providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(),
}));

const acceptPredictionMock = jest.fn();

describe('AcceptPrediction', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        acceptPredictionMock.mockRestore();
        jest.mocked(usePrediction).mockImplementation(
            () =>
                ({
                    userAnnotationsExist: true,
                    acceptPrediction: acceptPredictionMock,
                    enableMergingPredictionsPredicate: () => true,
                }) as unknown as PredictionContextProps
        );
    });

    const renderApp = async () => {
        const onCloseMock = jest.fn();

        await render(
            <AnnotationThresholdProvider minThreshold={0} selectedTask={null}>
                <AcceptPredictionButton styles={{}} onClose={onCloseMock}>
                    Accept
                </AcceptPredictionButton>
            </AnnotationThresholdProvider>
        );

        fireEvent.click(screen.getByRole('button'));

        expect(await screen.findByRole('dialog')).toBeInTheDocument();

        return { onCloseMock };
    };

    it('Accepts predictions and selects the next media item', async () => {
        const { onCloseMock } = await renderApp();

        fireEvent.click(await screen.findByRole('button', { name: /Replace/i }));
        await waitForElementToBeRemoved(screen.getByRole('dialog'));

        expect(acceptPredictionMock).toHaveBeenCalledWith(false, expect.anything());
        expect(onCloseMock).toHaveBeenCalled();
    });

    it('Accepts predictions ', async () => {
        const { onCloseMock } = await renderApp();

        fireEvent.click(screen.getByRole('button', { name: /Replace/i }));
        await waitForElementToBeRemoved(screen.getByRole('dialog'));

        expect(acceptPredictionMock).toHaveBeenCalledWith(false, expect.anything());
        expect(onCloseMock).toHaveBeenCalled();
    });

    it('Merge predictions and selects the next media item', async () => {
        const { onCloseMock } = await renderApp();

        fireEvent.click(screen.getByRole('button', { name: /Merge/i }));

        await waitForElementToBeRemoved(screen.getByRole('dialog'));

        expect(acceptPredictionMock).toHaveBeenCalledWith(true, expect.anything());
        expect(onCloseMock).toHaveBeenCalled();
    });

    it('Does not show merge button', async () => {
        jest.mocked(usePrediction).mockImplementation(
            () =>
                ({
                    userAnnotationsExist: true,
                    acceptPrediction: acceptPredictionMock,
                    enableMergingPredictionsPredicate: () => false,
                }) as unknown as PredictionContextProps
        );

        await renderApp();

        expect(screen.queryByRole('button', { name: /merge/i })).not.toBeInTheDocument();

        expect(acceptPredictionMock).not.toHaveBeenCalled();

        // Close the dialog to prevent a console.warn from this test
        fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
    });
});
