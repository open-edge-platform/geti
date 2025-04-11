// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
