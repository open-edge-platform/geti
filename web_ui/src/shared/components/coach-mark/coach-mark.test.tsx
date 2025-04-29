// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { FUX_NOTIFICATION_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { useTutorialEnablement } from '../../hooks/use-tutorial-enablement.hook';
import { DocsUrl, onPressLearnMore } from '../tutorials/utils';
import { CoachMark } from './coach-mark.component';
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

describe('Coach Mark', () => {
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

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('if showDismissAll is true - header, learn more, dismiss and dismiss all should be visible ', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);
        getStepInfoMock.mockReturnValue({
            stepNumber: undefined,
            totalCount: undefined,
        });
        render(<CoachMark {...parameters} />);

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
        render(<CoachMark {...parameters} />);

        expect(await screen.findByText('test description')).toBeInTheDocument();
        expect(screen.queryByText('test header')).toBeNull();
        expect(screen.queryByText('Dismiss')).toBeNull();
        expect(screen.getByText('Learn more')).toBeInTheDocument();
        expect(screen.queryByRole('button', { expanded: false })).toBeNull();
    });

    it('when docUrl is empty - Learn more button is hidden', () => {
        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, docUrl: undefined, showDismissAll: false });
        render(<CoachMark {...parameters} />);
        expect(screen.queryByText('Learn more')).toBeNull();

        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, docUrl: undefined });
        render(<CoachMark {...parameters} />);
        expect(screen.queryByText('Learn more')).toBeNull();
    });

    it('returns empty component when no description', () => {
        getCoachMarkMock.mockReturnValue({ ...mockedCoachMark, description: '' });
        render(<CoachMark {...parameters} />);

        expect(screen.queryByText('test header')).toBeNull();
        expect(screen.queryByText('test description')).toBeNull();
        expect(screen.queryByText('Dismiss')).toBeNull();
        expect(screen.queryByText('Learn more')).toBeNull();
        expect(screen.queryByRole('button', { expanded: false })).toBeNull();
    });

    it('executes learn more correctly', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<CoachMark {...parameters} />);

        const learnMoreBtn = await screen.findByText('Learn more');
        fireEvent.click(learnMoreBtn);

        expect(onPressLearnMoreMock).toHaveBeenCalled();
    });

    it('coach mark is showing a custom message', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<CoachMark {...parameters} customDescription='custom description' />);
        expect(await screen.findByText('custom description')).toBeVisible();
        expect(screen.queryByText('test description')).toBeNull();
    });

    it('coach mark is not showing back button when previousStepId is empty', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<CoachMark {...parameters} />);
        expect(screen.queryByRole('button', { name: 'Back button' })).not.toBeInTheDocument();
    });

    it('coach mark is not showing next button when nextStepId is empty', async () => {
        getCoachMarkMock.mockReturnValue(mockedCoachMark);

        render(<CoachMark {...parameters} />);
        expect(screen.queryByRole('button', { name: 'Next' })).not.toBeInTheDocument();
    });

    it('when nextStepId is not empty, "Next" button is displayed on a coach mark', async () => {
        getCoachMarkMock.mockReturnValue({
            ...mockedCoachMark,
            nextStepId: FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS,
        });
        render(<CoachMark {...parameters} />);

        const nextBtn = await screen.findByRole('button', { name: 'Next' });
        expect(nextBtn).toBeVisible();
    });

    it('when previousStepId is not empty, "Back" button is displayed on a coach mark', async () => {
        getCoachMarkMock.mockReturnValue({
            ...mockedCoachMark,
            previousStepId: FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS,
        });

        render(<CoachMark {...parameters} />);

        const prevBtn = await screen.findByRole('button', { name: 'Back button' });
        expect(prevBtn).toBeVisible();
    });
});
