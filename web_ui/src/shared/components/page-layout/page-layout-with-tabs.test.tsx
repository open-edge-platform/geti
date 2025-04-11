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

import { screen } from '@testing-library/react';

import { providersRender as render } from '../../../test-utils/required-providers-render';
import { TabItem } from '../tabs/tabs.interface';
import { PageLayoutWithTabs } from './page-layout-with-tabs.component';

describe('Page layout (with tabs)', () => {
    const tabs: TabItem[] = [
        {
            id: 'first',
            name: 'Tab1',
            key: 'tab1',
            children: <>Test</>,
        },
        {
            id: 'second',
            name: 'Tab2',
            key: 'tab2',
            children: <>This is content of the tab</>,
        },
    ];
    const label = 'test labels';
    const onSelectionChangedMock = jest.fn();

    it('Check if activeTab is properly shown', async () => {
        render(
            <PageLayoutWithTabs
                actionButton={<></>}
                tabs={tabs}
                tabsLabel={label}
                onSelectionChange={onSelectionChangedMock}
                activeTab={'tab2'}
                tabContentTopMargin={0}
            />
        );

        expect(screen.getByRole('tab', { name: 'Tab1' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Tab2' })).toBeInTheDocument();
        expect(screen.getByText('This is content of the tab')).toBeInTheDocument();
    });
});
