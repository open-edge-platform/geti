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

import '@wessberg/pointer-events';

import { fireEvent, render, screen } from '@testing-library/react';

import { Anchor } from './anchor.component';

describe('anchor', (): void => {
    const properties = {
        x: 10,
        y: 10,
        angle: 0,
        size: 10,
        zoom: 1,
        label: 'test-label',
        cursor: 'nw-resize',
        onComplete: jest.fn(),
        moveAnchorTo: jest.fn(),
    };

    it('calls moveAnchorTo when clicked upon and moved', () => {
        const moveAnchorCallback = jest.fn();
        render(
            <svg>
                <Anchor {...properties} moveAnchorTo={moveAnchorCallback}>
                    <rect></rect>
                </Anchor>
            </svg>
        );
        const anchorActor = screen.getByLabelText(properties.label);
        fireEvent.pointerDown(anchorActor);
        fireEvent.pointerMove(anchorActor, { clientX: 10, clientY: 10 });
        expect(moveAnchorCallback).toBeCalledTimes(1);
    });

    it('calls onComplete when clicked and released', () => {
        const onCompleteCallback = jest.fn();
        render(
            <svg>
                <Anchor {...properties} onComplete={onCompleteCallback}>
                    <rect></rect>
                </Anchor>
            </svg>
        );
        const anchorActor = screen.getByLabelText(properties.label);
        fireEvent.pointerDown(anchorActor);
        fireEvent.pointerMove(anchorActor, { clientX: 10, clientY: 10 });
        fireEvent.pointerUp(anchorActor);
        expect(onCompleteCallback).toBeCalledTimes(1);
    });
});
