// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { Label } from '../../../../../core/labels/label.interface';
import { getMockedKeypointNode } from '../../../../../test-utils/mocked-items-factory/mocked-keypoint';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { hover } from '../../../../../test-utils/utils';
import { SelectedProvider } from '../../../../annotator/providers/selected-provider/selected-provider.component';
import { ExpandablePointLabel } from './expandable-point-label.component';

describe('ExpandablePointLabel', () => {
    const mockedPoint = getMockedKeypointNode({ label: getMockedLabel({ name: 'mocked name' }) });

    it('does not render anything when the isVisible is false', () => {
        const { container } = render(
            <SelectedProvider>
                <ExpandablePointLabel isVisible={false} point={mockedPoint} />
            </SelectedProvider>
        );

        expect(container).toBeEmptyDOMElement();
    });

    it('renders the label element when is active (selected)', () => {
        render(
            <SelectedProvider selectedIds={[mockedPoint.label.id]}>
                <ExpandablePointLabel isVisible={false} point={mockedPoint} />
            </SelectedProvider>
        );

        expect(screen.getByText(mockedPoint.label.name)).toBeVisible();
    });

    it('label without prediction', () => {
        render(
            <SelectedProvider>
                <ExpandablePointLabel isVisible point={mockedPoint} />
            </SelectedProvider>
        );

        expect(screen.getByText(mockedPoint.label.name)).toBeInTheDocument();
        expect(screen.queryByLabelText('prediction icon')).not.toBeInTheDocument();
        expect(screen.queryByText('90%')).not.toBeInTheDocument();
    });

    it('label with prediction', () => {
        const labelName = 'mocked name';

        const predictionLabel = getMockedKeypointNode({
            label: {
                ...getMockedLabel({ name: labelName }),
                score: 0.5,
                source: { modelId: 'latest', modelStorageId: 'storage_id', userId: undefined },
            } as Label,
        });
        render(
            <SelectedProvider>
                <ExpandablePointLabel isVisible point={predictionLabel} />
            </SelectedProvider>
        );

        expect(screen.getByText('50%')).toBeVisible();
        expect(screen.getByText(labelName)).toBeVisible();
        expect(screen.getByLabelText('prediction icon')).toBeVisible();
    });

    it('renders children when selected', () => {
        const childText = 'child name';

        render(
            <SelectedProvider selectedIds={[mockedPoint.label.id]}>
                <ExpandablePointLabel isVisible point={mockedPoint}>
                    <div>{childText}</div>
                </ExpandablePointLabel>
            </SelectedProvider>
        );

        expect(screen.getByText(childText)).toBeVisible();
    });

    it('renders children when hovered', () => {
        const childText = 'child name';

        render(
            <SelectedProvider>
                <ExpandablePointLabel isVisible point={mockedPoint}>
                    <div>{childText}</div>
                </ExpandablePointLabel>
            </SelectedProvider>
        );

        hover(screen.getByTestId('point label container'));

        expect(screen.getByText(childText)).toBeVisible();
    });

    it('does not render children when options are disabled', () => {
        const childText = 'child name';

        render(
            <SelectedProvider selectedIds={[mockedPoint.label.id]}>
                <ExpandablePointLabel isVisible point={mockedPoint} isOptionsEnabled={false}>
                    <div>{childText}</div>
                </ExpandablePointLabel>
            </SelectedProvider>
        );

        expect(screen.queryByText(childText)).not.toBeInTheDocument();
    });
});
