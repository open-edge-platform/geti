// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

export const hover = (element: HTMLElement) => {
    fireEvent.mouseEnter(element);
};

export const unhover = (element: HTMLElement) => {
    fireEvent.mouseLeave(element);
};
