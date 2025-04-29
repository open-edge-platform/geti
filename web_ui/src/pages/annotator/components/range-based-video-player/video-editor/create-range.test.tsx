// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { CreateRange } from './create-range.component';

describe('CreateRange', () => {
    const videoFrame = getMockedVideoFrameMediaItem({});

    const labels = [
        getMockedLabel({ id: 'normal', name: 'Normal', color: 'var(--brand-moss)' }),
        getMockedLabel({ id: 'anomalous', name: 'Anomalous', color: 'var(--brand-coral-cobalt)' }),
    ];

    it('follows the active video frame', () => {
        const onSelectLabelForRange = jest.fn();
        const setRange = jest.fn();
        const range = null;
        const videoTimelineValue = 10;

        render(
            <CreateRange
                labels={labels}
                maxValue={videoFrame.metadata.frames}
                minValue={0}
                onSelectLabelForRange={onSelectLabelForRange}
                range={range}
                setRange={setRange}
                videoTimelineValue={videoTimelineValue}
            />
        );

        const left = screen.getByRole('slider', { name: /minimum/i });
        const right = screen.getByRole('slider', { name: /maximum/i });
        expect(left).toHaveValue(`${videoTimelineValue}`);
        expect(right).toHaveValue(`${videoTimelineValue}`);

        fireEvent.keyDown(right, { key: 'Right' });
        expect(setRange).toHaveBeenCalledWith([10, 11]);

        fireEvent.keyDown(left, { key: 'Left' });
        expect(setRange).toHaveBeenCalledWith([9, 10]);
    });

    it('Selects a label for a range', () => {
        const onSelectLabelForRange = jest.fn();
        const setRange = jest.fn();
        const range: [number, number] = [10, 100];
        const videoTimelineValue = 10;

        render(
            <CreateRange
                labels={labels}
                maxValue={videoFrame.metadata.frames}
                minValue={0}
                onSelectLabelForRange={onSelectLabelForRange}
                range={range}
                setRange={setRange}
                videoTimelineValue={videoTimelineValue}
            />
        );

        const left = screen.getByRole('slider', { name: /minimum/i });
        const right = screen.getByRole('slider', { name: /maximum/i });
        expect(left).toHaveValue(`${range[0]}`);
        expect(right).toHaveValue(`${range[1]}`);

        fireEvent.click(screen.getByLabelText(/Add range/i));

        expect(screen.getAllByRole('listitem')).toHaveLength(labels.length);

        fireEvent.click(screen.getByLabelText(`label item ${labels[0].name}`));
        expect(onSelectLabelForRange).toHaveBeenCalledWith(expect.objectContaining(labels[0]), undefined);
    });
});
