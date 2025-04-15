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

import { useRef } from 'react';

import { fireEvent, screen } from '@testing-library/react';

import { FUX_NOTIFICATION_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { useTutorialEnablement } from '../../hooks/use-tutorial-enablement.hook';
import { DocsUrl, onPressLearnMore } from '../tutorials/utils';
import { FuxNotification } from './fux-notification.component';
import { getFuxNotificationData, getStepInfo } from './utils';

jest.mock('../../hooks/use-tutorial-enablement.hook', () => {
    return {
        useTutorialEnablement: jest.fn(),
    };
});

jest.mock('./utils', () => {
    return {
        getFuxNotificationData: jest.fn(),
        getStepInfo: jest.fn(),
    };
});

jest.mock('../tutorials/utils', () => ({
    ...jest.requireActual('../tutorials/utils'),
    onPressLearnMore: jest.fn(),
}));

const mockedCoachMark = {
    header: 'test header',
    description: 'test description',
    docUrl: DocsUrl.ACTIVE_LEARNING,
    nextStepId: undefined,
    previousStepId: undefined,
    showDismissAll: true,
    tipPosition: undefined,
};

describe('FuxNotification', () => {
    const onPressLearnMoreMock = jest.mocked(onPressLearnMore);
    const getCoachMarkMock = jest.mocked(getFuxNotificationData);
    const getStepInfoMock = jest.mocked(getStepInfo);
    const useTutorialEnablementMock = jest.mocked(useTutorialEnablement);
    useTutorialEnablementMock.mockReturnValue({
        isOpen: true,
        close: jest.fn(),
        dismissAll: jest.fn(),
        changeTutorial: jest.fn(),
    });
    const parameters = {
        settingsKey: FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY,
        isLoading: false,
    };

    const mockTriggerRef = { current: null } as React.MutableRefObject<null>;
    const mockState = {
        isVisible: true,
        isOpen: true,
        setOpen: jest.fn(),
        open: jest.fn(),
        close: jest.fn(),
        toggle: jest.fn(),
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('if showDismissAll is true - header, learn more, dismiss and dismiss all should be visible ', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);
        getStepInfoMock.mockReturnValue({
            stepNumber: undefined,
            totalCount: undefined,
        });
        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);

        expect(await screen.findByText('test header')).toBeInTheDocument();
        expect(screen.getByText('test description')).toBeInTheDocument();
        expect(screen.getByText('Dismiss')).toBeInTheDocument();
        expect(screen.getByText('Learn more')).toBeInTheDocument();

        const moreBtn = screen.getByRole('button', { expanded: false });
        fireEvent.click(moreBtn);
        expect(screen.getByText('Dismiss all')).toBeDefined();
    });

    it('if showDismissAll is false - header,dismiss and dismiss all should be hidden ', async () => {
        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, showDismissAll: false });
        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);

        expect(await screen.findByText('test description')).toBeInTheDocument();
        expect(screen.queryByText('test header')).toBeNull();
        expect(screen.queryByText('Dismiss')).toBeNull();
        expect(screen.getByText('Learn more')).toBeInTheDocument();
        expect(screen.queryByRole('button', { expanded: false })).toBeNull();
    });

    it('when docUrl is empty - Learn more button is hidden', () => {
        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, docUrl: undefined, showDismissAll: false });
        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);
        expect(screen.queryByText('Learn more')).toBeNull();

        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, docUrl: undefined });
        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);
        expect(screen.queryByText('Learn more')).toBeNull();
    });

    it('returns empty component when no description', () => {
        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, description: '' });
        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);

        expect(screen.queryByText('test header')).toBeNull();
        expect(screen.queryByText('test description')).toBeNull();
        expect(screen.queryByText('Dismiss')).toBeNull();
        expect(screen.queryByText('Learn more')).toBeNull();
        expect(screen.queryByRole('button', { expanded: false })).toBeNull();
    });

    it('executes learn more correctly', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);

        const learnMoreBtn = await screen.findByText('Learn more');
        fireEvent.click(learnMoreBtn);

        expect(onPressLearnMoreMock).toHaveBeenCalled();
    });

    it('coach mark is showing a custom message', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(
            <FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters}>
                custom description
            </FuxNotification>
        );
        expect(await screen.findByText('custom description')).toBeVisible();
        expect(screen.queryByText('test description')).toBeNull();
    });

    it('coach mark is not showing back button when previousStepId is empty', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);
        expect(screen.queryByRole('button', { name: 'Back button' })).not.toBeInTheDocument();
    });

    it('coach mark is not showing next button when nextStepId is empty', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);
        expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument();
    });

    it('when nextStepId is not empty, "Next" button is displayed on a coach mark', async () => {
        getCoachMarkMock.mockReturnValue({
            ...mockedCoachMark,
            nextStepId: FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS,
        });
        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);

        const nextBtn = await screen.findByRole('button', { name: 'Next' });
        expect(nextBtn).toBeVisible();
    });

    it('when previousStepId is not empty, "Back" button is displayed on a coach mark', async () => {
        getCoachMarkMock.mockReturnValue({
            ...mockedCoachMark,
            previousStepId: FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS,
        });

        render(<FuxNotification triggerRef={mockTriggerRef} state={mockState} {...parameters} />);

        const prevBtn = await screen.findByRole('button', { name: 'Back button' });
        expect(prevBtn).toBeVisible();
    });
});
