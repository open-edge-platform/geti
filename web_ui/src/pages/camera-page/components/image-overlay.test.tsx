// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useOverlayTriggerState } from 'react-stately';

import { getMockedScreenshot } from '../../../test-utils/mocked-items-factory/mocked-camera';
import { providersRender } from '../../../test-utils/required-providers-render';
import { Screenshot } from '../../camera-support/camera.interface';
import { ImageOverlay } from './image-overlay.component';

const screenshotOne = getMockedScreenshot({ id: '1' });
const screenshotTwo = getMockedScreenshot({ id: '2' });

describe('ImageOverlay', () => {
    const renderAp = async ({
        defaultIndex = 0,
        screenshots = [],
        mockedDelete = jest.fn(),
    }: {
        defaultIndex?: number;
        screenshots?: Screenshot[];
        mockedDelete?: jest.Mock;
    }) => {
        const StateImageOverlay = () => {
            const state = useOverlayTriggerState({});
            return (
                <>
                    <ImageOverlay
                        screenshots={screenshots}
                        onDeleteItem={mockedDelete}
                        defaultIndex={defaultIndex}
                        dialogState={state}
                    />
                    <button onClick={state.toggle}>open overlay</button>
                </>
            );
        };

        return providersRender(<StateImageOverlay />);
    };

    it('empty items', async () => {
        await renderAp({ screenshots: [] });
        fireEvent.click(await screen.findByRole('button', { name: /open overlay/i }));

        expect(screen.queryByRole('button', { name: 'close preview' })).not.toBeInTheDocument();
    });

    it('single item, navigation options are hidden', async () => {
        await renderAp({ screenshots: [screenshotOne] });
        fireEvent.click(await screen.findByRole('button', { name: /open overlay/i }));

        expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotOne.id}` })).toBeVisible();

        expect(screen.queryByRole('button', { name: /next item/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /next item/i })).not.toBeInTheDocument();
    });

    it('calls onDelete', async () => {
        const mockedDelete = jest.fn();
        await renderAp({ screenshots: [screenshotOne], mockedDelete });
        fireEvent.click(await screen.findByRole('button', { name: /open overlay/i }));

        fireEvent.click(screen.getByRole('button', { name: /delete/i }));
        fireEvent.click(await screen.findByRole('button', { name: /delete/i }));

        expect(mockedDelete).toHaveBeenCalledWith(screenshotOne.id);
    });

    it('close preview', async () => {
        await renderAp({ screenshots: [screenshotOne] });

        fireEvent.click(await screen.findByRole('button', { name: /open overlay/i }));
        fireEvent.click(await screen.findByRole('button', { name: /close preview/i }));

        await waitFor(() => {
            expect(screen.queryByRole('button', { name: /close preview/i })).not.toBeInTheDocument();
        });
    });

    describe('multiple items', () => {
        it('gets back to the first item', async () => {
            const mockedScreenshot = [screenshotOne, screenshotTwo];

            await renderAp({ screenshots: mockedScreenshot });
            fireEvent.click(await screen.findByRole('button', { name: /open overlay/i }));

            expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotOne.id}` })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: /next item/i }));
            expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotTwo.id}` })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: /next item/i }));
            expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotOne.id}` })).toBeVisible();
        });

        it('moves to the last item', async () => {
            const mockedScreenshot = [screenshotOne, screenshotTwo];

            await renderAp({ screenshots: mockedScreenshot });
            fireEvent.click(await screen.findByRole('button', { name: /open overlay/i }));

            expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotOne.id}` })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: /previous item/i }));
            expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotTwo.id}` })).toBeVisible();

            fireEvent.click(screen.getByRole('button', { name: /previous item/i }));
            expect(screen.getByRole('img', { name: `full screen screenshot ${screenshotOne.id}` })).toBeVisible();
        });
    });
});
