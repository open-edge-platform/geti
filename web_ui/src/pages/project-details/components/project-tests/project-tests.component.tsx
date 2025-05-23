// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { paths } from '@geti/core/src/services/routes';
import { useNavigate } from 'react-router-dom';

import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { PageLayoutWithTabs } from '../../../../shared/components/page-layout/page-layout-with-tabs.component';
import { TabItem } from '../../../../shared/components/tabs/tabs.interface';
import { useActiveTab } from '../../../../shared/hooks/use-active-tab.hook';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { QuickInference } from './quick-inference/quick-inference.component';
import { Tests } from './tests.component';

enum TestsTabsKeys {
    TESTS = 'tests',
    LIVE_PREDICTION = 'live-prediction',
}

const TESTS_TABS_TO_URL_MAPPING = {
    [TestsTabsKeys.TESTS]: paths.project.tests.index,
    [TestsTabsKeys.LIVE_PREDICTION]: paths.project.tests.livePrediction,
};

export const ProjectTests = (): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const activeTab = useActiveTab(TestsTabsKeys.TESTS);
    const navigate = useNavigate();

    const TAB_ITEMS: TabItem[] = [
        {
            name: 'Tests',
            key: TestsTabsKeys.TESTS,
            id: idMatchingFormat(TestsTabsKeys.TESTS),
            children: <Tests />,
        },
        {
            name: 'Live prediction',
            key: TestsTabsKeys.LIVE_PREDICTION,
            id: idMatchingFormat(TestsTabsKeys.LIVE_PREDICTION),
            children: <QuickInference />,
        },
    ];

    const handleSelectionChange = (key: Key): void => {
        if (key === activeTab) return;

        navigate(TESTS_TABS_TO_URL_MAPPING[key as TestsTabsKeys](projectIdentifier));
    };

    return (
        <PageLayoutWithTabs
            activeTab={activeTab}
            tabs={TAB_ITEMS}
            tabsLabel={'Tests tabs'}
            tabsTopMargin={'size-100'}
            tabContentTopMargin={'size-100'}
            onSelectionChange={handleSelectionChange}
        />
    );
};
