// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { fireEvent, render, screen } from '@testing-library/react';

import { TemplatePose, Templates } from './templates.component';

describe('Templates', () => {
    const mockedRoi = { x: 0, y: 0, width: 1000, height: 1000 };

    const renderApp = (onAction: jest.Mock) => {
        render(
            <Provider theme={defaultTheme}>
                <Templates roi={mockedRoi} onAction={onAction} />
            </Provider>
        );
    };

    it.each([[TemplatePose.HumanPose], [TemplatePose.AnimalPose], [TemplatePose.HumanFace]])(
        'calls %s and onAction when "%s" is selected',
        (templateName) => {
            const mockedAction = jest.fn();

            renderApp(mockedAction);

            fireEvent.click(screen.getByRole('button', { name: 'templates list' }));
            fireEvent.click(screen.getByRole('menuitem', { name: templateName }));

            expect(mockedAction).toHaveBeenCalled();
        }
    );
});
