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

import { ReactElement } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render as renderElement, screen } from '@testing-library/react';

import { Explanation } from '../../../../core/annotations/prediction.interface';
import { ExplanationMap } from './explanation.component';
import { useCachedImages } from './use-cached-images.hook';

jest.mock('./use-cached-images.hook', () => {
    return {
        useCachedImages: jest.fn(),
    };
});

const render = async (ui: ReactElement) => {
    const client = new QueryClient();

    const container = renderElement(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);

    return container;
};

describe('Explanation', () => {
    const load = jest.fn();
    const explanation: Explanation = {
        labelsId: 'test-label',
        id: 'test-id',
        url: 'some-url',
        name: 'Explanation name',
        roi: {
            id: 'roi',
            shape: {
                x: 10,
                y: 10,
                type: 'RECTANGEL',
                width: 100,
                height: 50,
            },
        },
    };

    beforeEach(() => {
        (useCachedImages as jest.Mock).mockImplementation(() => ({
            load,
        }));
    });

    it('loads image when given explanation with url', async () => {
        await render(<ExplanationMap explanation={{ ...explanation, url: 'test-url' }} opacity={1} enabled />);

        expect(load).toBeCalledWith('test-url?raw=true');
    });

    it('shows image when given explanation with binary', async () => {
        await render(<ExplanationMap explanation={{ ...explanation, binary: 'a-binary' }} opacity={1} enabled />);

        expect(load).toBeCalledWith('data:image/jpeg;base64, a-binary');
    });

    it('shows nothing when not enabled', async () => {
        const { container } = await render(<ExplanationMap explanation={explanation} opacity={100} enabled={false} />);

        expect(container).toBeEmptyDOMElement();
    });

    it('shows loading animation when loading image', async () => {
        (useCachedImages as jest.Mock).mockImplementation(() => ({
            load,
            isLoading: true,
        }));

        await render(<ExplanationMap explanation={explanation} opacity={100} enabled />);

        expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('sets explanation opacity based on param', async () => {
        await render(<ExplanationMap explanation={explanation} opacity={50} enabled />);

        expect(screen.getByTestId('explanation-image')).toHaveStyle('opacity: 0.5');
    });

    it('renders explanation with dimensions and position of roi', async () => {
        await render(<ExplanationMap explanation={explanation} opacity={50} enabled />);

        const image = screen.getByTestId('explanation-image');
        const { shape } = explanation.roi;

        expect(image).toHaveStyle(`marginLeft: ${shape.x}px`);
        expect(image).toHaveStyle(`marginTop: ${shape.y}px`);
        expect(image).toHaveAttribute('width', `${explanation.roi.shape.width}`);
        expect(image).toHaveAttribute('height', `${explanation.roi.shape.height}`);
    });
});
