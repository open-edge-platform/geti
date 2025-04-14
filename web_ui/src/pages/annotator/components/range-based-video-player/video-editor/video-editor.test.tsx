// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import UndoRedoProvider from '../../../tools/undo-redo/undo-redo-provider.component';
import useUndoRedoState from '../../../tools/undo-redo/use-undo-redo-state';
import { getMockedVideoControls } from '../../video-player/video-controls/test-utils';
import { VideoEditor } from './video-editor.component';

const normalLabel = getMockedLabel({ id: 'normal', name: 'Normal', color: 'var(--brand-moss)' });
const anomalousLabel = getMockedLabel({ id: 'anomalous', name: 'Anomalous', color: 'var(--brand-coral-cobalt)' });
const labels = [normalLabel, anomalousLabel];

describe('VideoEditor', () => {
    const videoControls = getMockedVideoControls({});
    const videoFrame = getMockedVideoFrameMediaItem({});

    const getRangeSelectorToggleButton = () => screen.getByRole('button', { name: 'Range selector' });
    const addRange = () => fireEvent.click(screen.getByLabelText(/Add range/i));
    const getStartRangeThumb = () => screen.queryByLabelText('Start range');
    const getEndRangeThumb = () => screen.queryByLabelText('End range');

    const App = () => {
        const [ranges, setRanges, undoRedoState] = useUndoRedoState<LabeledVideoRange[]>([
            { start: 0, end: videoFrame.metadata.frames, labels: [labels[0]] },
        ]);

        return (
            <UndoRedoProvider state={undoRedoState}>
                <VideoEditor
                    videoFrame={videoFrame}
                    videoControls={videoControls}
                    labels={labels}
                    ranges={ranges}
                    setRanges={setRanges}
                    isAnomaly={false}
                />
            </UndoRedoProvider>
        );
    };

    it('renders', () => {
        render(<App />);

        const minimum = screen.getByRole('slider', { name: /Minimum/i });
        const maximum = screen.getByRole('slider', { name: /Maximum/i });
        const videoThumb = screen.getByRole('slider', { name: 'Seek in video' });

        fireEvent.change(videoThumb, { target: { value: 150 } });
        fireEvent.change(maximum, { target: { value: 200 } });
        fireEvent.change(minimum, { target: { value: 100 } });

        addRange();

        expect(screen.getAllByRole('listitem')).toHaveLength(labels.length);

        fireEvent.click(screen.getByLabelText(`label item ${anomalousLabel.name}`));

        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(3);

        fireEvent.click(screen.getByRole('button', { name: /Undo/i }));
        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(1);

        fireEvent.click(screen.getByRole('button', { name: /Redo/i }));
        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(3);

        fireEvent.click(screen.getByLabelText(/Click to change label from 100 to 200/i));

        expect(screen.getAllByRole('listitem')).toHaveLength(labels.length);
        fireEvent.click(screen.getByLabelText(`label item ${normalLabel.name}`));

        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(1);

        fireEvent.click(screen.getByRole('button', { name: /Undo/i }));
        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(3);
    });

    it('should render joined range when the second one is created from the edge of the first one', () => {
        render(<App />);

        fireEvent.change(screen.getByRole('slider', { name: /Maximum/i }), { target: { value: 200 } });
        addRange();
        fireEvent.click(screen.getByLabelText(`label item ${anomalousLabel.name}`));

        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(2);
        expect(screen.getByLabelText('Click to change label from 0 to 200')).toBeInTheDocument();
        expect(
            screen.getByLabelText(`Click to change label from 201 to ${videoFrame.metadata.frames}`)
        ).toBeInTheDocument();

        fireEvent.change(screen.getByRole('slider', { name: /Minimum/i }), { target: { value: 200 } });
        fireEvent.change(screen.getByRole('slider', { name: /Maximum/i }), { target: { value: 300 } });
        addRange();
        fireEvent.click(screen.getByLabelText(`label item ${anomalousLabel.name}`));

        expect(screen.getAllByLabelText(/Click to/)).toHaveLength(2);
        expect(screen.getByLabelText('Click to change label from 0 to 300')).toBeInTheDocument();
        expect(
            screen.getByLabelText(`Click to change label from 301 to ${videoFrame.metadata.frames}`)
        ).toBeInTheDocument();
    });

    it('should not display ranges when range selector is off', () => {
        render(<App />);

        const toggleButton = getRangeSelectorToggleButton();

        expect(getRangeSelectorToggleButton()).toHaveAttribute('aria-pressed', 'true');
        expect(getStartRangeThumb()).toBeInTheDocument();
        expect(getEndRangeThumb()).toBeInTheDocument();

        fireEvent.click(toggleButton);

        expect(getRangeSelectorToggleButton()).toHaveAttribute('aria-pressed', 'false');
        expect(getStartRangeThumb()).not.toBeInTheDocument();
        expect(getEndRangeThumb()).not.toBeInTheDocument();
    });
});
