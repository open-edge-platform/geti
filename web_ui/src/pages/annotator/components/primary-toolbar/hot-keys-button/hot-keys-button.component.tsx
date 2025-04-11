// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Content, Dialog, DialogTrigger } from '@adobe/react-spectrum';

import { Hotkeys } from '../../../../../assets/icons';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { Tabs } from '../../../../../shared/components/tabs/tabs.component';
import { TabItem } from '../../../../../shared/components/tabs/tabs.interface';
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
