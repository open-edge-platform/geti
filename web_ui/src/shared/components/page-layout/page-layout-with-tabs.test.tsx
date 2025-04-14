// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
