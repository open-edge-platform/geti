// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Dialog, DialogTrigger } from '@adobe/react-spectrum';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';
import { Tabs } from '@shared/components/tabs/tabs.component';
import { TabItem } from '@shared/components/tabs/tabs.interface';

import { Hotkeys } from '../../../../../assets/icons';
import { HotKeysList } from './hot-keys-list/hot-keys-list.component';

export const HotKeysButton = (): JSX.Element => {
    const ITEMS: TabItem[] = [
        {
            id: 'hotkeys',
            key: 'hotkeys',
            name: 'Hotkeys',
            children: <HotKeysList />,
        },
    ];

    const DISABLED_ITEMS = ['label-shortcuts'];

    return (
        <DialogTrigger type={'popover'} mobileType={'modal'} placement={'right'} hideArrow>
            <QuietActionButton id='hotkeys-button-id' aria-label='Show dialog with hotkeys'>
                <Hotkeys />
            </QuietActionButton>
            <Dialog minWidth={'60rem'} height={'40rem'}>
                <Content>
                    <Tabs
                        aria-label={'Hotkeys'}
                        items={ITEMS}
                        isQuiet={false}
                        disabledKeys={DISABLED_ITEMS}
                        height={'100%'}
                        panelOverflowY={'hidden'}
                    />
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
