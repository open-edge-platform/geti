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

import { fireEvent, Matcher, queryAllByAttribute, queryByAttribute, screen } from '@testing-library/react';

import { RegionOfInterest } from '../core/annotations/annotation.interface';
import { getImageData } from '../shared/canvas-utils';

export const getById = queryByAttribute.bind(null, 'id');
export const getAllWithMatchId = (container: HTMLElement, id: string): HTMLElement[] =>
    queryAllByAttribute('id', container, id, { exact: false });

export const onHoverTooltip = (element: HTMLElement | null): void => {
    if (element === null) {
        throw new Error('Element cannot be null');
    }

    fireEvent.mouseDown(document.body);
    fireEvent.mouseUp(document.body);
    fireEvent.mouseEnter(element);
};

export const onOutsideClick = (): void => {
    fireEvent.mouseDown(document.body);
    fireEvent.mouseUp(document.body);
};

export const MORE_THAN_100_CHARS_NAME =
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer malesuada rutrum felis nec rhoncus tincidunt.';

const mockROI = { x: 0, y: 0, width: 100, height: 100 };

export const getMockedROI = (roi: Partial<RegionOfInterest> = {}): RegionOfInterest => ({
    x: 0,
    y: 0,
    width: 100,
    height: 100,
    ...roi,
});

export const getMockedImage = (inputROI?: RegionOfInterest): ImageData => {
    const roi = inputROI ?? mockROI;

    const img = new Image(roi.width, roi.height);
    img.src = 'test-src';
    // @ts-expect-error This is necessary for some tests that change the origin of the roi
    img.x = roi.x;
    // @ts-expect-error This is necessary for some tests that change the origin of the roi
    img.y = roi.y;
    img.width = roi.width;
    img.height = roi.height;

    return getImageData(img);
};

export const checkTooltip = async (element: HTMLElement, tooltipText: Matcher) => {
    jest.useFakeTimers();

    onHoverTooltip(element);
    jest.advanceTimersByTime(750);

    expect(await screen.findByText(tooltipText)).toBeInTheDocument();
};

export const checkSpectrumButtonTooltip = async (element: HTMLElement, tooltipText: string | RegExp) => {
    fireEvent.click(element);
    fireEvent.mouseEnter(element);

    expect(await screen.findByText(tooltipText)).toBeInTheDocument();

    fireEvent.mouseLeave(element);
};

export const hover = (element: HTMLElement) => {
    fireEvent.mouseEnter(element);
};

export const unhover = (element: HTMLElement) => {
    fireEvent.mouseLeave(element);
};
