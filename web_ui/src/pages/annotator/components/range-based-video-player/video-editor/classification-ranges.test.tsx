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

import { fireEvent, screen } from '@testing-library/react';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { LABEL_BEHAVIOUR } from '../../../../../core/labels/label.interface';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ClassificationRanges } from './classification-ranges.component';

describe('ClassificationRanges', () => {
    const videoFrame = getMockedVideoFrameMediaItem({});
    const frames = videoFrame.metadata.frames;

    const labels = [
        getMockedLabel({
            id: 'normal',
            name: 'Normal',
            color: 'var(--brand-moss)',
            behaviour: LABEL_BEHAVIOUR.EXCLUSIVE,
        }),
        getMockedLabel({
            id: 'anomalous',
            name: 'Anomalous',
            color: 'var(--brand-coral-cobalt)',
            behaviour: LABEL_BEHAVIOUR.ANOMALOUS,
        }),
        getMockedLabel({ id: 'other', name: 'Other', color: 'var(--brand-moss)' }),
    ];

    const [normal, anomalous] = labels;

    it('allows to change a label on an existing range', () => {
        const ranges: LabeledVideoRange[] = [
            { start: 0, end: 100, labels: [normal] },
            { start: 101, end: 400, labels: [anomalous] },
            { start: 401, end: frames, labels: [normal] },
        ];

        const onSelectLabelForRange = jest.fn();

        render(
            <ClassificationRanges
                frames={frames}
                ranges={ranges}
                labels={labels}
                onSelectLabelForRange={onSelectLabelForRange}
            />
        );

        fireEvent.click(screen.getByLabelText(/Click to change label from 101 to 400/i));

        expect(screen.getAllByRole('listitem')).toHaveLength(labels.length);

        fireEvent.click(screen.getByLabelText(`label item ${labels[0].name}`));

        expect(onSelectLabelForRange).toHaveBeenCalledWith(expect.objectContaining(labels[0]), ranges[1]);
    });

    it('does not allow to change a label on an existing range when it is disabled', () => {
        const ranges: LabeledVideoRange[] = [
            { start: 0, end: 100, labels: [normal] },
            { start: 101, end: 400, labels: [anomalous] },
            { start: 401, end: frames, labels: [normal] },
        ];

        const onSelectLabelForRange = jest.fn();

        render(
            <ClassificationRanges
                frames={frames}
                ranges={ranges}
                labels={labels}
                onSelectLabelForRange={onSelectLabelForRange}
                isDisabled={true}
            />
        );

        fireEvent.click(screen.getByLabelText(/Click to change label from 101 to 400/i));

        expect(screen.queryAllByRole('listitem')).toHaveLength(0);
    });

    it('displays a suffix next to the label name when there is more than one label and none of them is anomalous', () => {
        const mockedLabels = [getMockedLabel({ id: 'cool-label' }), getMockedLabel({ id: 'cool-label-2' })];

        const ranges: LabeledVideoRange[] = [{ start: 0, end: 100, labels: mockedLabels }];

        const onSelectLabelForRange = jest.fn();

        render(
            <ClassificationRanges
                frames={frames}
                ranges={ranges}
                labels={mockedLabels}
                onSelectLabelForRange={onSelectLabelForRange}
            />
        );

        fireEvent.click(screen.getByLabelText(/Click to change label from 0 to 100/i));

        expect(screen.getAllByTestId('selection-suffix-id')).toHaveLength(mockedLabels.length);
    });

    it('does not display a suffix next to the label name when there is more than one label and they are anomalous', () => {
        const ranges: LabeledVideoRange[] = [
            { start: 0, end: 100, labels: [normal] },
            { start: 101, end: 400, labels: [anomalous] },
            { start: 401, end: frames, labels: [normal] },
        ];

        const onSelectLabelForRange = jest.fn();

        render(
            <ClassificationRanges
                frames={frames}
                ranges={ranges}
                labels={labels}
                onSelectLabelForRange={onSelectLabelForRange}
            />
        );

        fireEvent.click(screen.getByLabelText(/Click to change label from 0 to 100/i));

        expect(screen.queryAllByTestId('selection-suffix-id')).toHaveLength(0);
    });

    it('assigns label on click when there is only one available label', () => {
        const mockedLabels = [getMockedLabel({ id: 'cool-label' })];
        const ranges: LabeledVideoRange[] = [{ start: 0, end: 100, labels: mockedLabels }];

        const onSelectLabelForRange = jest.fn();

        render(
            <ClassificationRanges
                frames={frames}
                ranges={ranges}
                labels={mockedLabels}
                onSelectLabelForRange={onSelectLabelForRange}
                isDisabled={true}
            />
        );

        fireEvent.click(screen.getByLabelText(/Click to change label from 0 to 100/i));

        expect(screen.queryByLabelText('Label search results')).not.toBeInTheDocument();
        expect(onSelectLabelForRange).toHaveBeenCalledWith(expect.objectContaining(mockedLabels[0]), ranges[0]);
    });
});
