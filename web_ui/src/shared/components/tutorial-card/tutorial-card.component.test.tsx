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

import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { DocsUrl, onPressLearnMore } from '../tutorials/utils';
import { TutorialCard } from './tutorial-card.component';
import { getCardData } from './utils';

const mockedGetCardData = {
    header: 'test header',
    description: 'test description',
    docUrl: DocsUrl.ACTIVE_LEARNING,
};
jest.mock('./utils', () => {
    return {
        getCardData: jest.fn(),
    };
});
jest.mock('../tutorials/utils', () => ({
    ...jest.requireActual('../tutorials/utils'),
    onPressLearnMore: jest.fn(),
}));

describe('TutorialCard', () => {
    const getCardDataMock = jest.mocked(getCardData);
    const onPressLearnMoreMock = jest.mocked(onPressLearnMore);
    const mockDismiss = jest.fn();
    const mockDismissAll = jest.fn();
    const parameters = {
        id: TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_MULTIPLE_SELECTION,
        onPressDismiss: mockDismiss,
        onPressDismissAll: mockDismissAll,
        isLoading: false,
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders header, description correctly and all buttons correctly', () => {
        getCardDataMock.mockReturnValue(mockedGetCardData);
        render(<TutorialCard {...parameters} />);

        expect(screen.getByText('test header')).toBeInTheDocument();
        expect(screen.getByText('test description')).toBeInTheDocument();
        expect(screen.getByText('Dismiss')).toBeInTheDocument();
        expect(screen.getByText('Learn more')).toBeInTheDocument();

        const moreBtn = screen.getByRole('button', { expanded: false });
        fireEvent.click(moreBtn);
        expect(screen.getByText('Dismiss all')).toBeDefined();
    });

    it('when docUrl is empty - Learn more button is absent, rest of elements are rendered correctly', () => {
        getCardDataMock.mockReturnValue({ ...mockedGetCardData, docUrl: undefined });
        render(<TutorialCard {...parameters} />);

        expect(screen.getByText('test header')).toBeInTheDocument();
        expect(screen.getByText('test description')).toBeInTheDocument();
        expect(screen.getByText('Dismiss')).toBeInTheDocument();
        expect(screen.queryByText('Learn more')).toBeNull();

        const moreBtn = screen.getByRole('button', { expanded: false });
        fireEvent.click(moreBtn);
        expect(screen.getByText('Dismiss all')).toBeDefined();
    });

    it('returns empty component when no description', () => {
        getCardDataMock.mockReturnValue({ ...mockedGetCardData, description: '' });
        render(<TutorialCard {...parameters} />);

        expect(screen.queryByText('test header')).toBeNull();
        expect(screen.queryByText('test description')).toBeNull();
        expect(screen.queryByText('Dismiss')).toBeNull();
        expect(screen.queryByText('Learn more')).toBeNull();
    });

    it('executes learn more correctly', () => {
        getCardDataMock.mockReturnValue(mockedGetCardData);
        render(<TutorialCard {...parameters} />);

        const learnMoreBtn = screen.getByText('Learn more');

        fireEvent.click(learnMoreBtn);
        expect(onPressLearnMoreMock).toHaveBeenCalledWith(
            'https://docs.geti.intel.com/on-prem/2.6/guide/annotations/annotation-editor.html#active-learning'
        );
    });

    it('executes callback correctly', () => {
        getCardDataMock.mockReturnValue(mockedGetCardData);
        render(<TutorialCard {...parameters} />);

        const dismissButton = screen.getByText('Dismiss');

        fireEvent.click(dismissButton);
        expect(mockDismiss).toHaveBeenCalled();

        const moreBtn = screen.getByRole('button', { expanded: false });
        fireEvent.click(moreBtn);
        const dismissAllBtn = screen.getByText('Dismiss all');
        fireEvent.click(dismissAllBtn);
        expect(mockDismissAll).toHaveBeenCalled();
    });
});
