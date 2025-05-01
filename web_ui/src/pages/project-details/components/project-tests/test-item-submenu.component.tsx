// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MenuTriggerPopup } from '@shared/components/menu-trigger-popup/menu-trigger-popup.component';

interface TestItemSubmenuProps {
    id: string;
    testName: string;
    handleDeleteTest: () => void;
}

export const TestItemSubmenu = ({ id, testName, handleDeleteTest }: TestItemSubmenuProps): JSX.Element => {
    const DELETE = 'Delete';
    const items = [DELETE];

    return (
        <MenuTriggerPopup
            menuTriggerId={`row-${id}-menu-id`}
            question={`Are you sure you want to delete test "${testName}"?`}
            onPrimaryAction={handleDeleteTest}
            items={items}
        />
    );
};
